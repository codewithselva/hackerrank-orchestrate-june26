# Evaluation Report

## Summary
Sample claims processed: 20

## Metrics
- evidence_standard_met: 80.0% exact match
- issue_type: 45.0% exact match
- object_part: 50.0% exact match
- claim_status: 65.0% exact match
- valid_image: 90.0% exact match
- severity: 40.0% exact match
- risk_flags: 35.0% exact match
- supporting_image_ids: 55.0% exact match

## Mismatch examples
---
User ID: user_002
Image paths: images/sample/case_002/img_1.jpg;images/sample/case_002/img_2.jpg
Claim object: car
Differences:
- evidence_standard_met: expected='false', predicted='true'
- issue_type: expected='broken_part', predicted='scratch'
- claim_status: expected='not_enough_information', predicted='supported'
- severity: expected='unknown', predicted='low'
- risk_flags: expected='wrong_object;claim_mismatch;manual_review_required', predicted='cropped_or_obstructed;low_light_or_glare'
- supporting_image_ids: expected='img_1;img_2', predicted='img_1'
---
User ID: user_004
Image paths: images/sample/case_003/img_1.jpg;images/sample/case_003/img_2.jpg
Claim object: car
Differences:
- severity: expected='medium', predicted='low'
- supporting_image_ids: expected='img_1', predicted='img_2;img_1'
---
User ID: user_007
Image paths: images/sample/case_004/img_1.jpg
Claim object: car
Differences:
- severity: expected='medium', predicted='high'
- risk_flags: expected='none', predicted='cropped_or_obstructed;low_light_or_glare'
---
User ID: user_005
Image paths: images/sample/case_005/img_1.jpg;images/sample/case_005/img_2.jpg
Claim object: car
Differences:
- claim_status: expected='contradicted', predicted='supported'
- severity: expected='low', predicted='high'
- risk_flags: expected='claim_mismatch;user_history_risk;manual_review_required', predicted='cropped_or_obstructed;low_light_or_glare;user_history_risk;manual_review_required'
- supporting_image_ids: expected='img_1', predicted='img_1;img_2'
---
User ID: user_006
Image paths: images/sample/case_006/img_1.jpg
Claim object: car
Differences:
- evidence_standard_met: expected='false', predicted='true'
- issue_type: expected='unknown', predicted='crack'
- claim_status: expected='not_enough_information', predicted='supported'
- severity: expected='unknown', predicted='high'
- risk_flags: expected='wrong_angle;damage_not_visible', predicted='manual_review_required'
- supporting_image_ids: expected='none', predicted='img_1'
---
User ID: user_003
Image paths: images/sample/case_007/img_1.jpg;images/sample/case_007/img_2.jpg
Claim object: car
Differences:
- risk_flags: expected='blurry_image', predicted='none'
---
User ID: user_008
Image paths: images/sample/case_008/img_1.jpg
Claim object: car
Differences:
- evidence_standard_met: expected='true', predicted='false'
- issue_type: expected='broken_part', predicted='scratch'
- object_part: expected='front_bumper', predicted='door'
- valid_image: expected='false', predicted='true'
- severity: expected='high', predicted='medium'
- risk_flags: expected='claim_mismatch;non_original_image;user_history_risk;manual_review_required', predicted='user_history_risk;manual_review_required;claim_mismatch'
---
User ID: user_010
Image paths: images/sample/case_010/img_1.jpg;images/sample/case_010/img_2.jpg
Claim object: laptop
Differences:
- object_part: expected='hinge', predicted='screen'
- risk_flags: expected='none', predicted='cropped_or_obstructed;low_light_or_glare'
- supporting_image_ids: expected='img_1', predicted='img_1;img_2'
---
User ID: user_011
Image paths: images/sample/case_011/img_1.jpg
Claim object: laptop
Differences:
- object_part: expected='keyboard', predicted='screen'
---
User ID: user_012
Image paths: images/sample/case_012/img_1.jpg;images/sample/case_012/img_2.jpg
Claim object: laptop
Differences:
- severity: expected='low', predicted='medium'
- supporting_image_ids: expected='img_2', predicted='img_1'