"""What other modules may use from identity.

`learner_auth` guards an endpoint for signed-in learners and puts a `Learner` (the
anonymous learner ID and interface language, no personal data) on `request.auth`.
`router` and `problem_for` serve the API wiring.
"""

from .api import router
from .auth import Learner, learner_auth
from .problems import problem_for

__all__ = ["Learner", "learner_auth", "problem_for", "router"]
