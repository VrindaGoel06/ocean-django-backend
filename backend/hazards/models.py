from django.db import models
from common.models import (
    TimeStampedModel,
    hazardSet,
    actionStatusSet,
    GeoVideo,
    verificationStatusSet,
)
from django.contrib.auth import get_user_model
from common.AI.core import client as AIclient
from common.AI import NLP
import json


class UserReport(TimeStampedModel):
    user_submit_type = models.IntegerField(
        "Hazard according to user", choices=hazardSet, null=False
    )
    user_text = models.CharField(null=False, blank=False)
    user_ip = models.GenericIPAddressField(
        "IP used to make the report", null=False, blank=False
    )
    user_userAgent = models.CharField(
        "UserAgent of the browser", null=False, blank=False
    )
    user_platform = models.CharField("Platform of the user", null=False, blank=False)
    user_device_language = models.CharField(
        "Device language of the user's device", null=False, blank=False
    )
    action_status = models.IntegerField(
        "Action status",
        choices=actionStatusSet,
        null=False,
        default=actionStatusSet.TO_BE_STARTED,
    )
    user = models.ForeignKey(
        get_user_model(), on_delete=models.SET_NULL, default=None, null=True
    )
    geovideo = models.OneToOneField(
        GeoVideo, on_delete=models.CASCADE, primary_key=True
    )
    verification = models.IntegerField(
        "Status of the verification",
        choices=verificationStatusSet,
        null=False,
        default=verificationStatusSet.NOT_SYSTEM_PROCESSED,
    )
    coins = models.PositiveSmallIntegerField(
        "Coins given till now", null=False, default=0
    )
    proccessed_data = models.JSONField(
        "Output from the AI models", null=True, default=None
    )
    type = models.IntegerField(
        "Hazard according to system",
        choices=hazardSet,
        null=True,
        default=None,
    )
    severity = models.PositiveSmallIntegerField(
        # desc"Severity between 1-100 based on the AI model system",
        null=True,
        default=None,
    )
    confidence = models.PositiveSmallIntegerField(
        # "Confidence between 1-100 on the system based on the AI model system",
        null=True,
        default=None,
    )
    language = models.CharField(max_length=5, null=True, default=None, blank=False)

    def __str__(self):
        return self.user_ip

    def process(self):
        processed_data = []
        for model in NLP.MODELS:
            try:
                completion = AIclient.chat.completions.create(
                    model=f"{model}:price",
                    messages=[
                        {"role": "system", "content": NLP.SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": NLP.USER_PROMPT_TEMPLATE.format(
                                json.dumps(self.user_submit_type),
                                json.dumps(self.user_text),
                            ),
                        },
                    ],
                    temperature=0.1,
                    max_tokens=500,
                )
                data = completion.choices[0].message.content
                if data is None:
                    continue
                data = data.replace("`", "").replace("json", "").replace("\n", "")
                processed_data.append(json.loads(data))
            except:
                continue
        self.proccessed_data = processed_data
        types = []
        severities = []
        confidences = []
        languages = []
        for item in processed_data:
            try:
                item_type = int(item["type"])
            except:
                continue
            try:
                severity = int(item["severity"])
            except:
                continue
            try:
                confidence = int(item["confidence"])
            except:
                continue
            try:
                language = str(item["input_language"])
            except:
                continue
            types.append(item_type)
            confidences.append(confidence)
            severities.append(severity)
            languages.append(language)
        final_type = NLP.combine_type(
            types,
            confidences,
            severities,
            user_type=self.user_submit_type,
            user_weight=80,
        )
        final_severity = NLP.combine_severity(severities, confidences)
        final_confidence = NLP.combine_confidence(
            confidences, severities, min_penalty_k=0.3
        )
        lang2id = {}
        for s in languages:
            k = s.strip().lower()
            if k not in lang2id:
                lang2id[k] = len(lang2id)  # or len(lang2id)+1 for 1-based
        languages_ids = [lang2id[s.strip().lower()] for s in languages]
        id2lang = {i: lang for lang, i in lang2id.items()}
        final_language_id = NLP.combine_type(languages_ids, confidences)
        final_language = id2lang[final_language_id]
        self.type = final_type
        self.severity = final_severity
        self.confidence = final_confidence
        self.language = final_language
        self.action_status = actionStatusSet.NEXT_STAGE
        self.save()
