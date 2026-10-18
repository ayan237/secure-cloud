<#
.SYNOPSIS
Safely clean up AWS resources (S3 bucket, CloudFront distribution).

.DESCRIPTION
- Empties and deletes the S3 bucket.
- Requires explicit user confirmation.
#>

param(
    [string]$BucketName = "securecloud-portfolio",
    [string]$Region = "us-east-1"
)

$confirmation = Read-Host "WARNING: This will permanently delete s3://$BucketName. Proceed? (y/N)"
if ($confirmation -ne 'y' -and $confirmation -ne 'Y') {
    Write-Host "Cleanup cancelled."
    exit 0
}

Write-Host "Emptying bucket s3://$BucketName..."
aws s3 rm "s3://$BucketName" --recursive

Write-Host "Deleting bucket s3://$BucketName..."
aws s3api delete-bucket --bucket $BucketName --region $Region

Write-Host "Cleanup complete."
