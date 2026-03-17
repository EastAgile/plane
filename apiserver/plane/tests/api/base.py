# Third party imports
from rest_framework.test import APITestCase, APIClient

# Module imports
from plane.db.models import User


class BaseAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient(
            HTTP_USER_AGENT="plane/test",
            REMOTE_ADDR="10.10.10.10",
        )


class AuthenticatedAPITest(BaseAPITest):
    def setUp(self):
        super().setUp()

        ## Create Dummy User
        self.email = "user@plane.so"
        user = User.objects.create(email=self.email)
        user.set_password("user@123")
        user.save()

        # Set user
        self.user = user

        # Set Up User ID
        self.user_id = user.id

        # Authenticate via session (force_login bypasses password check)
        self.client.force_login(user)
