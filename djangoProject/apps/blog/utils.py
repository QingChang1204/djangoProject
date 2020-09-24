import json
import logging
import random
import uuid
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from django_redis.pool import ConnectionFactory
from blog.search import SearchByEs
from aliyunsdkcore.request import RpcRequest
from aliyunsdkcore.client import AcsClient
from models import VerifyCode

logger = logging.getLogger(__name__)
search = SearchByEs()


class DecodeConnectionFactory(ConnectionFactory):

    def get_connection(self, params):
        params['decode_responses'] = True
        return super().get_connection(params)


def custom_response(data, status, *args, **kwargs):
    return HttpResponse(json.dumps(data, ensure_ascii=False), status=status, *args, **kwargs)


class SendSMS:
    REGION = "cn-hangzhou"
    PRODUCT_NAME = "Dysmsapi"
    DOMAIN = "dysmsapi.aliyuncs.com"

    def __init__(self):
        self.acs_client = AcsClient(settings.ALIYUN_SMS_ACCESS_ID, settings.ALIYUN_SMS_ACCESS_KEY, self.REGION)

    def send_sms(self, template_param=None, **kwargs):
        sms_request = RpcRequest(self.PRODUCT_NAME, '2017-05-25', 'SendSms')

        sms_request.__params = {}
        sms_request.__params.update(**kwargs)

        if template_param is not None:
            sms_request.__params.update({'TemplateParam': template_param})
        sms_request.set_query_params(sms_request.__params)

        sms_response = self.acs_client.do_action_with_exception(sms_request)

        return sms_response

    def send_code_message(self, phone):
        code = ''.join(str(random.choice(range(10))) for _ in range(6))
        __business_id = uuid.uuid1()
        params = '{"code":"' + code + '"}'
        response = self.send_sms(template_param=params,
                                 OutId=__business_id,
                                 PhoneNumbers=str(phone),
                                 SignName=settings.SMS_SIGN_NAME,
                                 TemplateCode=settings.SMS_TEMPLATE_CODE,
                                 )
        return_code = json.loads(response.decode('utf-8')).get('Code', 0)
        if return_code == 'OK':
            code_info = VerifyCode.objects.filter(
                email=phone,
            ).first()
            if code_info is None:
                VerifyCode.objects.create(
                    email=phone,
                    code=code,
                    sent=timezone.now()
                )
            else:
                code_info.code = code
                code_info.sent = timezone.now()
                code_info.save()
            return True, return_code
        else:
            return False, return_code

    def send_warning_message(self, phone):
        __business_id = uuid.uuid1()
        response = self.send_sms(OutId=__business_id,
                                 SignName=settings.SMS_SIGN_NAME,
                                 PhoneNumbers=phone,
                                 TemplateCode=settings.SMS_TEMPLATE_CODE,
                                 )

        return_code = json.loads(response.decode('utf-8')).get('Code', 0)
        if return_code == 'OK':
            return True, return_code
        else:
            return False, return_code


send_sms = SendSMS()
