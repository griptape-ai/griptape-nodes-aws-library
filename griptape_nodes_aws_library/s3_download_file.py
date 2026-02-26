import os
import subprocess
from typing import Any

from griptape_nodes.exe_types.core_types import Parameter, ParameterMode
from griptape_nodes.exe_types.node_types import ControlNode


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

    def validate_before_node_run(self) -> list[Exception] | None:
        exceptions = []
        for key in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"):
            try:
                self.get_config_value(service="AWS", value=key)
            except Exception as e:
                exceptions.append(e)
        return exceptions if exceptions else None

    def process(self) -> None:
        s3_uri = self.parameter_values["s3_uri"]
        local_path = self.parameter_values["local_path"]

        if not s3_uri or not s3_uri.startswith("s3://"):
            raise ValueError(f"{self.name}: s3_uri must be a valid S3 URI starting with 's3://'")
        if not local_path:
            raise ValueError(f"{self.name}: local_path is required")

        env = os.environ.copy()
        for key in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_DEFAULT_REGION", "AWS_SESSION_TOKEN"):
            try:
                value = self.get_config_value(service="AWS", value=key)
                if value:
                    env[key] = value
            except Exception:
                pass

        result = subprocess.run(
            ["aws", "s3", "cp", s3_uri, local_path],
            capture_output=True,
            text=True,
            env=env,
        )
        if result.returncode != 0:
            raise ValueError(f"{self.name}: AWS CLI error: {result.stderr.strip()}")

        self.parameter_output_values["downloaded_path"] = local_path
