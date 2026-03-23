from typing import Any
from urllib.parse import urlparse

import httpx

from griptape_nodes.exe_types.core_types import Parameter, ParameterMode
from griptape_nodes.exe_types.node_types import ControlNode
from griptape_nodes.exe_types.param_types.parameter_bool import ParameterBool
from griptape_nodes.files.file import File

from griptape_nodes_aws_library.aws.aws_session import start_session, validate_aws_credentials


class S3DownloadFile(ControlNode):
    def __init__(self, name: str, metadata: dict[str, Any] | None = None, **kwargs) -> None:
        node_metadata = {
            "category": "S3",
            "description": "Download a file from S3 to local storage",
        }
        if metadata:
            node_metadata.update(metadata)
        super().__init__(name=name, metadata=node_metadata, **kwargs)

        self.add_parameter(
            ParameterBool(
                name="use_presigned_url",
                default_value=False,
                tooltip="Toggle between S3 URI and a presigned HTTPS URL",
                allow_output=False,
            )
        )
        self.add_parameter(
            Parameter(
                name="s3_uri",
                input_types=["str"],
                type="str",
                default_value="",
                allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY},
                tooltip="S3 URI (e.g. s3://mybucket/myfile.txt)",
            )
        )
        self.add_parameter(
            Parameter(
                name="presigned_url",
                input_types=["str"],
                type="str",
                default_value="",
                allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY},
                tooltip="Presigned HTTPS URL for the S3 object",
            )
        )
        self.hide_parameter_by_name("presigned_url")
        self.add_parameter(
            Parameter(
                name="local_path",
                input_types=["str"],
                type="str",
                default_value="",
                allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY},
                tooltip="Local destination path for the downloaded file",
            )
        )
        self.add_parameter(
            Parameter(
                name="downloaded_path",
                output_type="str",
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="Local path of the downloaded file",
            )
        )

    def after_value_set(self, parameter: Parameter, value: Any) -> None:
        if parameter.name == "use_presigned_url":
            if value:
                self.hide_parameter_by_name("s3_uri")
                self.show_parameter_by_name("presigned_url")
            else:
                self.show_parameter_by_name("s3_uri")
                self.hide_parameter_by_name("presigned_url")
        return super().after_value_set(parameter, value)

    def validate_before_workflow_run(self) -> list[Exception] | None:
        use_presigned_url = self.parameter_values.get("use_presigned_url", False)
        if use_presigned_url:
            return None
        return validate_aws_credentials(self.name)

    def process(self) -> None:
        use_presigned_url = self.parameter_values.get("use_presigned_url", False)
        local_path = self.parameter_values["local_path"]

        if not local_path:
            raise ValueError(f"{self.name}: local_path is required")

        if use_presigned_url:
            url = self.parameter_values.get("presigned_url", "")
            if not url:
                raise ValueError(f"{self.name}: presigned_url is required")
            response = httpx.get(url)
            response.raise_for_status()
            content = response.content
        else:
            s3_uri = self.parameter_values.get("s3_uri", "")
            if not s3_uri:
                raise ValueError(f"{self.name}: s3_uri is required")
            if not s3_uri.startswith("s3://"):
                raise ValueError(f"{self.name}: s3_uri must start with s3://")
            parsed = urlparse(s3_uri)
            bucket = parsed.netloc
            key = parsed.path.lstrip("/")
            session = start_session(self.name)
            s3_client = session.client("s3")
            content = s3_client.get_object(Bucket=bucket, Key=key)["Body"].read()

        written_path = File(local_path).write_bytes(content)

        self.parameter_output_values["downloaded_path"] = str(written_path)
