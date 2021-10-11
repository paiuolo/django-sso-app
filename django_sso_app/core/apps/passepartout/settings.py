import string

from django.conf import settings


all_chars = string.ascii_letters + string.digits
forbidden_chars = ('I', 'l', '1', '|', '0', 'O')

permitted_chars = [el for el in all_chars if el not in forbidden_chars]

CODE_LENGTH = getattr(settings, 'COUPONS_CODE_LENGTH', 36)
CODE_CHARS = getattr(settings, 'COUPONS_CODE_CHARS', permitted_chars)

# "".join(random.choice(CODE_CHARS) for i in range(CODE_LENGTH))
