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
                tooltip="S3 URI of the file to download (e.g. s3://mybucket/myfile.txt)",
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
        return validate_aws_credentials(self.name)

    def process(self) -> None:
        s3_uri = self.parameter_values["s3_uri"]
        local_path = self.parameter_values["local_path"]

        if not s3_uri or not s3_uri.startswith("s3://"):
            raise ValueError(f"{self.name}: s3_uri must be a valid S3 URI starting with 's3://'")
        if not local_path:
            raise ValueError(f"{self.name}: local_path is required")

        parsed = urlparse(s3_uri)
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")

        session = start_session(self.name)
        s3_client = session.client("s3")
        content = s3_client.get_object(Bucket=bucket, Key=key)["Body"].read()

        written_path = File(local_path).write_bytes(content)

        self.parameter_output_values["downloaded_path"] = written_path
