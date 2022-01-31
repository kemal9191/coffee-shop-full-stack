import json
import os
from re import A
from flask import request, _request_ctx_stack, abort
from functools import wraps
from jose import jwt
from urllib.request import urlopen

import rsa


AUTH0_DOMAIN = os.environ.get('AUTH0_DOMAIN')
ALGORITHMS = os.environ.get('ALGORITHMS')
API_AUDIENCE = os.environ.get('API_AUDIENCE')

    ## AuthError Exception

class AuthError(Exception):
    '''
    AuthError Exception
    A standardized way to communicate auth failure modes
    '''
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


    ## Auth Header


def get_token_auth_header():
    '''
    Fetches JWT
    '''
    auth_header = request.headers.get('Authorization', None)

    if auth_header is None:
       raise AuthError({
           "code": "header_not_found",
           "decription": "Authorization header is expected"
       }, 401)

    auth_header_array = auth_header.split(" ")

    if len(auth_header_array)!= 2:
        raise AuthError({
            "code": "invalid_header",
            "description": "Header is not valid"
        }, 401)
    
    elif auth_header_array[0].lower() != 'bearer':
        raise AuthError({
            "code": "invalid_header",
            "description": "Authorization header must start with bearer"
        }, 401)
    
    return auth_header_array[1]


def check_permissions(permission, payload):
    '''
    Fetches Authorization header and checks permissions
    '''
    if 'permissions' not in payload:
        raise AuthError({
            "code": "invalid_claims",
            "description": "Permissions must be included in JWT"
        }, 400)
    
    if permission not in payload['permissions']:
        raise AuthError({
            "code": "unauthorized",
            "description": "User has no authority to this action"
        }, 401)

    return True


def verify_decode_jwt(token):
    '''
    Fetches Authorization header and verifies JWT
    '''
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())

        #Getting the data in the header
    unverified_header = jwt.get_unverified_header(token)

        #Choosing the key
    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError({
            "code": "invalid_header",
            "description": "Header is not valid"
        }, 401)

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                "kty": key['kty'],
                "kid": key['kid'],
                "use": key['use'],
                "n": key['n'],
                "e": key['e']
            }
    
        #Verification Process
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({
                "code": "expired_token",
                "description": "Token expired"
            }, 401)
        
        except jwt.JWTClaimsError:
            raise AuthError({
                "code": "invalid_claims",
                "description": "Claims are not correct. Please check parameters in audience and issuer"
            }, 401)

        except Exception:
            raise AuthError({
                "code": "invalid_header",
                "description": "Header is not valid"
            }, 400)
    
    raise AuthError({
        "code": "invalid_header",
        "description": "Key not found"
    }, 400)


def requires_auth(permission=''):
    '''
    Handles with authorization
    '''
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            try:
                payload = verify_decode_jwt(token)
                check_permissions(permission, payload)
            except:
                abort(401)
            return f(payload, *args, **kwargs)
        return wrapper
    return requires_auth_decorator