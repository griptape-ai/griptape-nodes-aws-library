# Griptape Nodes: AWS Library

AWS nodes for the [Griptape Nodes](https://www.griptapenodes.com/) engine. Provides nodes for interacting with AWS services using boto3.

## Nodes

### S3

#### S3 Download File

Downloads a file from S3 to local storage.

| Parameter | Mode | Type | Description |
|-----------|------|------|-------------|
| `s3_uri` | Input / Property | `str` | S3 URI of the file to download (e.g. `s3://mybucket/myfile.txt`) |
| `local_path` | Input / Property | `str` | Local destination path for the downloaded file |
| `downloaded_path` | Output | `str` | Local path of the downloaded file |

#### S3 Upload File

Uploads a file from local storage to S3.

| Parameter | Mode | Type | Description |
|-----------|------|------|-------------|
| `local_path` | Input / Property | `str` | Local path of the file to upload |
| `s3_uri` | Input / Property | `str` | S3 URI destination (e.g. `s3://mybucket/myfile.txt`) |
| `uploaded_uri` | Output | `str` | S3 URI of the uploaded file |

## Credentials

This library requires AWS credentials configured in Griptape Nodes secrets:

| Secret | Required | Description |
|--------|----------|-------------|
| `AWS_ACCESS_KEY_ID` | Yes | AWS access key ID |
| `AWS_SECRET_ACCESS_KEY` | Yes | AWS secret access key |
| `AWS_DEFAULT_REGION` | Yes | AWS region (e.g. `us-east-1`) |
| `AWS_SESSION_TOKEN` | No | Session token for temporary credentials (STS, SSO, assumed roles) |

`AWS_SESSION_TOKEN` is only required when using temporary credentials. Leave it empty for long-term IAM user credentials.

## Installation

1. Clone the repository into your Griptape Nodes workspace directory:

   ```bash
   cd `gtn config show workspace_directory`
   git clone https://github.com/griptape-ai/griptape-nodes-aws-library.git
   ```

2. Add the library in the Griptape Nodes Editor:

   - Open Settings and navigate to **Libraries**
   - Click **+ Add Library**
   - Enter the path to the library JSON file:
     `<workspace_directory>/griptape-nodes-aws-library/griptape_nodes_library.json`
   - Close Settings and click **Refresh Libraries**

3. Configure AWS credentials in Settings > **API Keys & Secrets** using the key names listed above.

4. Restart the Griptape Nodes engine to pick up the new secrets.

## Troubleshooting

**`InvalidClientTokenId` / `InvalidAccessKeyId`**: Verify your credentials are correct. If using temporary credentials, ensure `AWS_SESSION_TOKEN` is also set. Restart the engine after updating secrets.

**`FileNotFoundError` on upload**: The `local_path` parameter accepts workspace-relative paths, absolute paths, and localhost URLs produced by other nodes.

**Library not appearing**: Verify the path to `griptape_nodes_library.json` is correct and that the library was refreshed after adding.
