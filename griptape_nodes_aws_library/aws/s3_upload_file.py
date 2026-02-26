from typing import Any
from urllib.parse import urlparse

from griptape_nodes.exe_types.core_types import Parameter, ParameterMode
from griptape_nodes.exe_types.node_types import ControlNode
from griptape_nodes.files.file import File

from griptape_nodes_aws_library.aws.aws_session import start_session, validate_aws_credentials


class S3UploadFile(ControlNode):
    def __init__(self, name: str, metadata: dict[str, Any] | None = None, **kwargs) -> None:
        node_metadata = {
            "category": "S3",
            "description": "Upload a file from local storage to S3",
        }
        if metadata:
            node_metadata.update(metadata)
        super().__init__(name=name, metadata=node_metadata, **kwargs)

        self.add_parameter(
            Parameter(
                name="local_path",
                input_types=["str"],
                type="str",
                default_value="",
                allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY},
                tooltip="Local path of the file to upload",
            )
        )
        self.add_parameter(
            Parameter(
                name="s3_uri",
                input_types=["str"],
                type="str",
                default_value="",
                allowed_modes={ParameterMode.INPUT, ParameterMode.PROPERTY},
                tooltip="S3 URI destination (e.g. s3://mybucket/myfile.txt)",
            )
        )
        self.add_parameter(
            Parameter(
                name="uploaded_uri",
                output_type="str",
                allowed_modes={ParameterMode.OUTPUT},
                tooltip="S3 URI of the uploaded file",
            )
        )

    def validate_before_workflow_run(self) -> list[Exception] | None:
        return validate_aws_credentials(self.name)

    def process(self) -> None:
        local_path = self.parameter_values["local_path"]
        s3_uri = self.parameter_values["s3_uri"]

        if not local_path:
            raise ValueError(f"{self.name}: local_path is required")
        if not s3_uri or not s3_uri.startswith("s3://"):
            raise ValueError(f"{self.name}: s3_uri must be a valid S3 URI starting with 's3://'")

        parsed = urlparse(s3_uri)
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")

        content = File(local_path).read_bytes()

        session = start_session(self.name)
        s3_client = session.client("s3")
        s3_client.put_object(Bucket=bucket, Key=key, Body=content)

        self.parameter_output_values["uploaded_uri"] = s3_uri
