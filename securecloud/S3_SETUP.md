# Using Amazon S3 with SecureCloud

This guide connects the locally running SecureCloud backend to a private Amazon S3 bucket. The backend already stores encrypted blocks and manifests in S3; the browser does not connect to AWS directly.

## What is stored where

- The backend encrypts each file with AES-256-GCM, then uploads encrypted blocks and a manifest beneath `files/` in the bucket.
- The per-file decryption key is kept in the local `securecloud_keys` directory, not in S3. Keep that directory backed up securely. Losing a key makes its file unrecoverable, even if its S3 objects still exist.
- The API, frontend, and key store remain on your computer. This setup does not deploy the application to AWS.
- Existing files in the in-memory mock are not migrated to S3 and disappear when the backend process stops. Upload original files again after connecting S3.

## 1. Check Free Tier and cost first

Free Tier eligibility and included amounts depend on your AWS account, account age, region, and current AWS offer. Check the [AWS Free Tier page](https://aws.amazon.com/free/) and [Amazon S3 pricing](https://aws.amazon.com/s3/pricing/) for your account before uploading data. Charges can apply for storage, requests, data transfer, and other AWS services; Free Tier is not a guarantee of a zero bill.

Create an AWS Budget alert with a low threshold and billing notifications. Alerts can be delayed and do not stop spending. For a small demo, avoid enabling CloudFront, replication, or other services unless you specifically need them.

## 2. Create a private bucket

In the AWS console:

1. Open **Amazon S3 → Buckets → Create bucket**.
2. Choose a globally unique bucket name and the AWS Region you intend to use.
3. Keep **Block all public access** enabled. This app does not need public bucket access or S3 static website hosting.
4. Keep the default bucket-owner-enforced object ownership and default server-side encryption (SSE-S3) enabled.
5. Leave versioning disabled for this small demo unless you need recovery from accidental deletes; old versions continue to use storage.
6. Create the bucket. Note the exact name and region.

Do not put access keys or encryption keys in a bucket policy, frontend code, or the repository.

## 3. Configure local AWS credentials and least-privilege access

Install the [AWS CLI for Windows](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html). Use AWS IAM Identity Center/SSO if your account has it configured:

```powershell
aws configure sso
aws sso login
aws sts get-caller-identity
```

Otherwise, use an IAM identity dedicated to this demo, not your root account. Give it only the policy below, replacing `YOUR_BUCKET_NAME` with the bucket you created. Use a bucket dedicated to SecureCloud: the bucket-level list permission is needed by the app's `HeadBucket` startup check. Configure credentials with `aws configure` when prompted, and never commit or share the generated credentials.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListSecureCloudObjects",
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME"
    },
    {
      "Sid": "ManageSecureCloudObjects",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME/files/*"
    }
  ]
}
```

The list permission allows listing object names in this dedicated bucket; the object read/write/delete permissions are limited to the app's `files/` prefix. If you use a named AWS CLI profile, set it in the PowerShell window that will run the backend:

```powershell
$env:AWS_PROFILE = "your-profile-name"
aws sts get-caller-identity
```

The `get-caller-identity` command should succeed and show the expected AWS account/identity before proceeding.

## 4. Set SecureCloud configuration

For this checkout, `backend/config.py` loads `.env` from `C:\cc-mini\.env` (the parent workspace directory) and stores local keys under `C:\cc-mini\securecloud_keys`. Create or edit that `.env` file:

```dotenv
AWS_REGION=us-east-1
S3_BUCKET=your-globally-unique-bucket-name
```

Use the actual bucket region and name. `.env` is ignored by Git; do not commit it. AWS credentials should remain in the AWS CLI credential store or another AWS credential provider, not in `.env`.

## 5. Start the app and verify that it really uses S3

From `C:\cc-mini\securecloud`, activate the project's virtual environment if applicable, then start the backend:

```powershell
uvicorn backend.main:app --reload
```

Open the UI or use the API to upload a small test file. Confirm objects appear in the S3 console under the bucket's `files/` prefix, including encrypted block objects and `manifest.json`. You can also inspect the prefix with the CLI:

```powershell
aws s3api list-objects-v2 `
  --bucket "your-globally-unique-bucket-name" `
  --prefix "files/" `
  --region "us-east-1"
```

Then test listing, download, and delete through the app, and confirm the objects are gone after deletion. The local key file for the test upload is deleted by the app when that file is deleted.

**Important:** the current `Storage` implementation catches S3 initialization and bucket-check errors and switches to an in-memory mock. A healthy API response alone does not prove that S3 is being used. If the bucket stays empty, check the backend's AWS profile/identity, bucket name, region, and IAM permissions, then restart the backend and verify again. Do not upload sensitive or irreplaceable files until you have confirmed objects reach the intended bucket and tested key backup/recovery.

## 6. Local key backup and future deployment

Back up `C:\cc-mini\securecloud_keys` using a secure method separate from the S3 bucket, and keep the backup access-controlled. The S3 objects alone are not sufficient to decrypt files. Do not copy keys into the frontend, commit them, or place them in the same bucket as the encrypted files.

If you later move the backend to a server, securely migrate the corresponding key files and configure that server's AWS role/credentials and bucket/region. S3 does not automatically synchronize the local key store.

## Troubleshooting

- **App starts, but S3 has no `files/` objects:** the backend may have fallen back to its in-memory mock. Verify the AWS identity, bucket region/name, and permissions; restart and upload again.
- **`AccessDenied`:** ensure the identity has the two policy statements above for the exact bucket. Bucket-level listing is separate from object access.
- **Bucket not found or wrong region:** ensure `S3_BUCKET` matches exactly and `AWS_REGION` matches the bucket's region.
- **Downloads fail after moving machines or reinstalling:** restore the matching local key file for each file ID; it cannot be reconstructed from S3.

## Safe cleanup

To remove the demo data, use the app's delete endpoint for each file or delete only the `files/` prefix from the correct application bucket after checking the bucket name. For example, inspect the target first:

```powershell
aws s3 ls "s3://your-globally-unique-bucket-name/files/" --recursive
```

Do not use `scripts/cleanup_aws.ps1` for this application bucket: that script defaults to the separate `securecloud-portfolio` bucket and is intended for portfolio resources. Emptying a bucket or deleting a bucket is permanent; double-check the account and exact bucket before any manual cleanup.
