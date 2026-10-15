# Goal
Keep the image intact and remove only the logo and text overlaid on the image. Keep the image clean and preserve the original content.

# Constraints
- STRICT RULE: Do not change face, hair, expression, pose, layout, or background.
- Remove only logos and embedded text (watermark).
- Keep image clean, preserve original content.

# Prohibited (exclusions)
- No change to face, hair, expression, pose, layout, or background.

# Ownership Rule
- Requires ownership_confirmed=true before running.
- Write audit_logs (user, job, time, IP hash).
- If ownership not confirmed → reject.

# Expected Result
Clean image, no logo/text overlay, original content fully preserved.
