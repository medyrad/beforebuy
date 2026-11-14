from rest_framework import serializers

from analysis.domain.money import MoneyValidationError, normalize_budget, normalize_toman


class AnalysisInputSerializer(serializers.Serializer):
    product_label = serializers.CharField(min_length=2, max_length=120, trim_whitespace=True)
    price_toman = serializers.JSONField()
    budget_toman = serializers.JSONField(allow_null=True)
    answers = serializers.DictField()

    def to_internal_value(self, data):
        if isinstance(data, dict):
            unknown = sorted(set(data) - set(self.fields))
            if unknown:
                raise serializers.ValidationError({key: ["Unknown field."] for key in unknown})
        return super().to_internal_value(data)

    def validate_price_toman(self, value):
        try:
            return normalize_toman(value, allow_zero=False)
        except MoneyValidationError as exc:
            raise serializers.ValidationError(exc.code) from exc

    def validate_budget_toman(self, value):
        try:
            return normalize_budget(value)
        except MoneyValidationError as exc:
            raise serializers.ValidationError(exc.code) from exc

    def validate_answers(self, value):
        required = {"Q-001", "Q-002", "Q-003", "Q-004", "Q-006"}
        allowed_keys = required | {"F-001", "F-002", "F-003"}
        missing = sorted(required - set(value))
        if missing:
            raise serializers.ValidationError(f"Missing required answers: {', '.join(missing)}")
        unknown_keys = sorted(set(value) - allowed_keys)
        if unknown_keys:
            raise serializers.ValidationError(f"Unknown answer IDs: {', '.join(unknown_keys)}")
        choices = {
            "Q-001": {"NO_DEVICE", "UNUSABLE", "SERIOUS_PROBLEM", "MINOR_PROBLEM", "WORKS_WELL", "UNKNOWN"},
            "Q-002": {"RESTORE_ESSENTIAL_ACCESS", "SOLVE_MAJOR_LIMIT", "ENABLE_IMPORTANT_NEW_USE",
                      "SOLVE_MINOR_LIMIT", "PERSONAL_ENJOYMENT", "NO_CLEAR_BENEFIT", "UNKNOWN"},
            "Q-004": {"WITHIN_48_HOURS", "WITHIN_2_WEEKS", "WITHIN_3_MONTHS", "FLEXIBLE", "UNKNOWN"},
        }
        for key, allowed in choices.items():
            if value[key] not in allowed:
                raise serializers.ValidationError({key: ["Unsupported choice."]})
        self._validate_multiselect(
            value, "Q-003",
            {"CALLS_MESSAGES", "PHOTO_VIDEO", "WORK_STUDY", "GAMING", "ACCESSIBILITY", "GENERAL_USE", "OTHER", "UNKNOWN"},
            maximum=3, exclusive={"UNKNOWN"},
        )
        self._validate_multiselect(
            value, "Q-006",
            {"REPAIR_CURRENT", "WAIT", "KEEP_CURRENT", "CHANGE_REQUIREMENTS", "ACCEPTED_TARGET_TRADEOFFS", "NONE", "UNKNOWN"},
            maximum=7, exclusive={"NONE", "UNKNOWN"},
        )
        followups = [key for key in value if key.startswith("F-")]
        if len(followups) > 3:
            raise serializers.ValidationError("At most three follow-up answers are allowed.")
        if "F-001" in value and (
            not isinstance(value["F-001"], str) or not value["F-001"].strip() or len(value["F-001"].strip()) > 240
        ):
            raise serializers.ValidationError({"F-001": ["Must be 1 to 240 characters."]})
        if "F-002" in value:
            allowed_f2 = choices["Q-002"] | choices["Q-004"] | {"STILL_UNKNOWN"}
            if value["F-002"] not in allowed_f2:
                raise serializers.ValidationError({"F-002": ["Unsupported choice."]})
        if "F-003" in value and value["F-003"] not in {
            "USER_REPORTS_IT_FITS", "USER_REPORTS_IT_DOES_NOT_FIT", "NO_INFORMATION"
        }:
            raise serializers.ValidationError({"F-003": ["Unsupported choice."]})
        return value

    @staticmethod
    def _validate_multiselect(value, key, allowed, *, maximum, exclusive):
        selected = value[key]
        if not isinstance(selected, list) or not 1 <= len(selected) <= maximum:
            raise serializers.ValidationError({key: [f"Select between 1 and {maximum} unique values."]})
        if len(set(selected)) != len(selected) or any(item not in allowed for item in selected):
            raise serializers.ValidationError({key: ["Contains duplicate or unsupported choices."]})
        if exclusive.intersection(selected) and len(selected) != 1:
            raise serializers.ValidationError({key: ["NONE/UNKNOWN must be selected alone."]})


class FeedbackInputSerializer(serializers.Serializer):
    report_revision_id = serializers.UUIDField()
    rating = serializers.IntegerField(min_value=1, max_value=5)


class AnalysisUpdateSerializer(AnalysisInputSerializer):
    expected_input_revision = serializers.IntegerField(min_value=1, write_only=True)


class ReanalysisSerializer(serializers.Serializer):
    expected_input_revision = serializers.IntegerField(min_value=1)
    expected_report_revision_id = serializers.UUIDField()
