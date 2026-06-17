from keycloak import KeycloakOpenID
import logging
from http.client import HTTPConnection

HTTPConnection.debuglevel = 1

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

keycloak_openid = KeycloakOpenID(server_url="https://auth-staging.tol.sanger.ac.uk/auth/",
                                 client_id="testclient",
                                 realm_name="dev",
                                 client_secret_key="tFQpyt6E87FyCujCPz2aS4DGnTUbhozq",
                                 pool_maxsize=15,
                                 verify=False
                                )

# auth_url = keycloak_openid.auth_url(
#     redirect_uri="https://localhost:3011/callback",
#     scope="email",
#     state="123456")

# print("Login URL:", auth_url)

access_token = keycloak_openid.token(
    grant_type='authorization_code',
    # code='fe002b41-727d-4c5f-4a1b-f68bd4519c59.50c9b5f2-ee4f-f333-da9b-0aab90216e57.d6080eee-ad78-497c-87bc-3fedcff92d80',
    redirect_uri="https://localhost:3011/callback",
    username='test',
    password='test'
)
