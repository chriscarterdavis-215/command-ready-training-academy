# Command Ready Training Academy — Platform Design

## Public brand
Command Ready Training Academy — Knowledge. Judgment. Readiness.
Independent online law-enforcement training, initially focused on Texas patrol legal refreshers.

## User experiences
**Learner:** assigned course, module progress, scenario practice, final assessment, completion history.
**Agency administrator (future):** agency roster, invitations, assigned courses, results and downloadable completion report restricted to their agency.
**Platform administrator:** course authoring and publishing, agency onboarding, audit and support, cross-agency operational management.

## Data model (future)
organizations(id, name, status)
users(id, email, password_hash, mfa, status)
memberships(user_id, organization_id, role)
courses(id, slug, title)
course_versions(id, course_id, version, published_at)
enrollments(id, user_id, organization_id, course_version_id, assigned_at)
module_progress(enrollment_id, module_id, completed_at)
exam_attempts(enrollment_id, exam_version, started_at, submitted_at, score)
certificates(enrollment_id, unique_verification_id, issued_at, revoked_at)
audit_events(actor_id, organization_id, action, timestamp)

Every enrollment, progress and reporting API must validate organization membership and role on the server. Agency admins must never see another agency's data. Cross-agency isolation must be tested before external deployment.

## Suggested launch sequence
Private demo -> internal technical/legal review -> isolated pilot agency -> hosted production service -> additional agencies.
No TCOLE hours until provider/course eligibility and reporting procedures are formally confirmed.
