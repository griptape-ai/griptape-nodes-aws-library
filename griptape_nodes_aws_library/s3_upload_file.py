from typing import Any
from urllib.parse import urlparse

import boto3  # pyright: ignore[reportMissingImports]

from griptape_nodes.exe_types.core_types import Parameter, ParameterMode
from griptape_nodes.exe_types.node_types import ControlNode
from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes

AWS_ACCESS_KEY_ID_ENV_VAR = "AWS_ACCESS_KEY_ID"
AWS_SECRET_ACCESS_KEY_ENV_VAR = "AWS_SECRET_ACCESS_KEY"  # noqa: S105
AWS_DEFAULT_REGION_ENV_VAR = "AWS_DEFAULT_REGION"


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

    def start_session(self) -> boto3.Session:
        """Creates a boto3 session using AWS credentials from the secrets manager."""
        aws_access_key_id = GriptapeNodes.SecretsManager().get_secret(AWS_ACCESS_KEY_ID_ENV_VAR)
        aws_secret_access_key = GriptapeNodes.SecretsManager().get_secret(AWS_SECRET_ACCESS_KEY_ENV_VAR)
        aws_default_region = GriptapeNodes.SecretsManager().get_secret(AWS_DEFAULT_REGION_ENV_VAR)

        try:
            session = boto3.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=aws_default_region,
            )
        except Exception as e:
            msg = f"Failed to create AWS session for node {self.name}. Please check your AWS credentials and region."
            raise RuntimeError(msg) from e
        return session

    def validate_before_workflow_run(self) -> list[Exception] | None:
        exceptions = []
        for key in (AWS_ACCESS_KEY_ID_ENV_VAR, AWS_SECRET_ACCESS_KEY_ENV_VAR, AWS_DEFAULT_REGION_ENV_VAR):
            value = GriptapeNodes.SecretsManager().get_secret(key)
            if not value:
                exceptions.append(ValueError(f"{self.name}: AWS credential '{key}' is not configured."))
        return exceptions if exceptions else None

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

        session = self.start_session()
        s3_client = session.client("s3")
        s3_client.upload_file(local_path, bucket, key)

        self.parameter_output_values["uploaded_uri"] = s3_uri
