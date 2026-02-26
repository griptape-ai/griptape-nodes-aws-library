import boto3  # pyright: ignore[reportMissingImports]

from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes

AWS_ACCESS_KEY_ID_ENV_VAR = "AWS_ACCESS_KEY_ID"
AWS_SECRET_ACCESS_KEY_ENV_VAR = "AWS_SECRET_ACCESS_KEY"  # noqa: S105
AWS_DEFAULT_REGION_ENV_VAR = "AWS_DEFAULT_REGION"


def start_session(node_name: str) -> boto3.Session:
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
        msg = f"Failed to create AWS session for node {node_name}. Please check your AWS credentials and region."
        raise RuntimeError(msg) from e
    return session


def validate_aws_credentials(node_name: str) -> list[Exception] | None:
    """Checks that all required AWS credential secrets are configured."""
    exceptions = []
    for key in (AWS_ACCESS_KEY_ID_ENV_VAR, AWS_SECRET_ACCESS_KEY_ENV_VAR, AWS_DEFAULT_REGION_ENV_VAR):
        value = GriptapeNodes.SecretsManager().get_secret(key)
        if not value:
            exceptions.append(ValueError(f"{node_name}: AWS credential '{key}' is not configured."))
    return exceptions if exceptions else None
