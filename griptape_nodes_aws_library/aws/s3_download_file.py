import urllib.request
from typing import Any
from urllib.parse import urlparse

from griptape_nodes.exe_types.core_types import Parameter, ParameterMode
from griptape_nodes.exe_types.node_types import ControlNode
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
            Parameter(
                name="s3_uri",
                input_types=["str"],
                type="str",
                default_value="",
                allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY},
                tooltip="S3 URI (e.g. s3://mybucket/myfile.txt) or presigned HTTPS URL",
            )
        )
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

    def validate_before_workflow_run(self) -> list[Exception] | None:
        s3_uri = self.parameter_values.get("s3_uri", "")
        if s3_uri and s3_uri.startswith("https://"):
            return None
        return validate_aws_credentials(self.name)

    def process(self) -> None:
        s3_uri = self.parameter_values["s3_uri"]
        local_path = self.parameter_values["local_path"]

        if not s3_uri:
            raise ValueError(f"{self.name}: s3_uri is required")
        if not local_path:
            raise ValueError(f"{self.name}: local_path is required")

        if s3_uri.startswith("https://"):
            with urllib.request.urlopen(s3_uri) as response:  # noqa: S310
                content = response.read()
        elif s3_uri.startswith("s3://"):
            parsed = urlparse(s3_uri)
            bucket = parsed.netloc
            key = parsed.path.lstrip("/")
            session = start_session(self.name)
            s3_client = session.client("s3")
            content = s3_client.get_object(Bucket=bucket, Key=key)["Body"].read()
        else:
            raise ValueError(f"{self.name}: s3_uri must be an S3 URI (s3://) or a presigned HTTPS URL (https://)")

        written_path = File(local_path).write_bytes(content)

        self.parameter_output_values["downloaded_path"] = str(written_path)
