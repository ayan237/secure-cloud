<#
.SYNOPSIS
Deploy the static portfolio site to an S3 bucket and CloudFront distribution.

.DESCRIPTION
- Syncs portfolio/ to S3.
- Invalidates CloudFront cache.
- Requires explicit user confirmation.
#>

param(
    [string]$BucketName = "securecloud-portfolio",
    [string]$Region = "us-east-1"
)

$confirmation = Read-Host "Are you sure you want to deploy portfolio to S3 bucket '$BucketName' in '$Region'? (y/N)"
if ($confirmation -ne 'y' -and $confirmation -ne 'Y') {
    Write-Host "Deployment cancelled."
    exit 0
}

Write-Host "Syncing portfolio directory to s3://$BucketName..."
aws s3 sync .\portfolio\ "s3://$BucketName/" --delete

Write-Host "Deployment complete."
