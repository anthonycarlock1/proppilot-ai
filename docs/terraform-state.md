# Terraform remote state

All seven PropPilot roots use the dedicated `anthony-proppilot-tfstate-388691194728` S3 bucket in `us-east-1`, with distinct default-workspace keys:

| Root | Key |
| --- | --- |
| state-backend | proppilot/state-backend/terraform.tfstate |
| registry | proppilot/registry/terraform.tfstate |
| hosting | proppilot/hosting/terraform.tfstate |
| urgency-hosting | proppilot/urgency-hosting/terraform.tfstate |
| tickets | proppilot/tickets/terraform.tfstate |
| runtime | proppilot/runtime/terraform.tfstate |
| ci | proppilot/ci/terraform.tfstate |

The bucket has versioning, AES256 server-side encryption, all public-access blocks, bucket-owner-enforced ownership and a deny for non-TLS requests. Terraform `prevent_destroy` and `force_destroy = false` protect ordinary bucket teardown. These are safeguards, not protection against an administrator deliberately changing configuration or deleting versions. No state expiration lifecycle is configured: old versions remain available for recovery and incur small storage/request charges.

Native S3 locking uses `use_lockfile = true`; Terraform 1.10+ is required. The `.tflock` object is temporary and must remain deletable. S3 Object Lock is not enabled. The backend pins the expected AWS account and contains no credentials. Use an authorized AWS profile or short-lived credentials; never put keys in backend configuration.

References: [HashiCorp S3 backend](https://developer.hashicorp.com/terraform/language/backend/s3), [backend migration and backups](https://developer.hashicorp.com/terraform/language/backend), [AWS backend guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/terraform-aws-provider-best-practices/backend.html).

## Normal operation

```bash
terraform -chdir=terraform/registry init -input=false
terraform -chdir=terraform/registry plan -lock-timeout=60s
```

Run from the project root. Substitute the required root. Hosting roots also require the existing immutable `image_uri` from their deployment guides. Review saved plans before applying. Backend credentials need `s3:ListBucket` for the relevant prefix, `s3:GetObject`/`s3:PutObject` for its state key, and `s3:GetObject`/`s3:PutObject`/`s3:DeleteObject` for the matching `.tflock` key. Resource provisioning requires separate provider permissions. There is no CI principal or automatic deployment permission grant in this milestone. Use the default workspace; different stages should have explicitly provisioned resources and state keys rather than accidentally sharing this state.

State may contain sensitive data. Do not print it in CI, publish it, or commit state, plans, `.terraform`, or recovery copies. Migration backups are held in gitignored `.state-backups/pre-s3/`, mode 0600 inside a mode 0700 directory. Keep them protected until recovery policy is agreed; these local backups are not an independent offsite backup.

## Migration procedure

1. Stop concurrent Terraform operations. Verify the AWS account and inspect existing local resource addresses.
2. Bootstrap `terraform/state-backend` locally: initialize, save/review a plan, and apply only that plan. This creates the bucket and five protection/configuration resources; it does not change application resources.
3. Back up every original local state before editing backend configuration.
4. Add each root's S3 backend. For an existing local state, use `terraform init -migrate-state` and confirm the copy. Do not use `-reconfigure` to replace migration. For a fresh checkout after migration, normal `terraform init` connects to the existing remote state.
5. Pull the migrated state privately and compare the complete resources and outputs to the backup; record lineage/serial changes explicitly. Terraform migration preserves metadata where the state managers support it; this run reset lineage/serial while preserving resource snapshots and outputs. Do not force-push an old lineage to conceal that change. Check bucket versioning/encryption/public access and object existence without publishing state bodies.
6. Run a normal refresh-enabled plan on every root; require exit code zero with `-detailed-exitcode`. A migration is not permission to apply drift or resource replacements.
7. Bootstrap state is also migrated into its own bucket. A new installation must create the bucket before enabling that root's S3 backend; see the bootstrap note below.

## Bootstrap note for a new account

The committed configuration refers to Anthony's existing assessment account, not a reusable cross-account deployment. For a deliberately new environment, choose a new bucket/account and update all backend files. Temporarily omit only `terraform/state-backend/backend.tf` while creating the backend in an isolated working copy; then restore it and migrate the bootstrap state. Never apply an empty or newly initialized local state against the existing deployment. The bucket cannot be its own backend until it exists.

## Recovery and teardown

For a lock conflict, wait for the operation that holds it. Use `terraform force-unlock LOCK_ID` only after identifying the owner and proving that process has stopped. Never bypass a live lock with `-lock=false`.

For state damage, freeze writes, privately download the current object and the selected earlier S3 version, inspect lineage/resources/serial, and review against actual AWS resources. Preserve the current version before any recovery. Recovery via `terraform state push` can overwrite authoritative state; do not use `-force` routinely or blindly restore an old version. Refresh/plan and resolve drift before resuming changes.

For ordinary project teardown, destroy each application root from a reviewed plan while keeping the backend available. Ticket deletion protection and nonempty ECR repositories require explicit handling. Keep the state bucket and version history after workload removal. Backend destruction is a separate deliberate operation: migrate state out, verify protected backups, remove lifecycle protection only with approval, and handle all object versions explicitly. No backend deletion is part of the current workflow.

The original five roots were migrated from local state; the runtime root was initialized directly against S3 for the EKS milestone. Its zero-change follow-up plan is recorded in [EKS evidence](eks-verification.json).

Verification results for the original migration are recorded in [remote-state-verification.json](remote-state-verification.json). An unverified plan/configuration alone is not evidence of migration.

Migration metadata behavior is documented in [Terraform 1.15.6 state migration implementation](https://github.com/hashicorp/terraform/blob/v1.15.6/internal/states/statemgr/migrate.go): serial/lineage are preserved where supported by both state managers. The initial strict metadata check stopped on the registry root; full snapshot equality was verified before proceeding.
