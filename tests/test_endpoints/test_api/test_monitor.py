from sqlalchemy.orm import Session

from planitor.endpoints.api.monitor import set_subscription_council_types
from planitor.models import (
    Council,
    CouncilTypeEnum,
    Municipality,
    Subscription,
    SubscriptionTypeEnum,
)
from planitor.schemas.monitor import SubscriptionCouncilTypeForm


def test_set_subscription_council_types(
    db: Session, subscription: Subscription, municipality: Municipality
):

    # Add another council to the fixture, because exploring the logic tree requires more
    # than one council
    db.add(
        Council(
            name="Skipulagsfulltrui",
            council_type=CouncilTypeEnum.skipulagsfulltrui,
            municipality=municipality,
        )
    )
    db.commit()

    assert not subscription.council_types
    assert subscription.type == SubscriptionTypeEnum.case

    _Form = SubscriptionCouncilTypeForm

    # Test setting one council type
    set_subscription_council_types(
        subscription,
        [_Form(name="byggingarfulltrui")],
    )

    assert subscription.council_types == [CouncilTypeEnum.byggingarfulltrui]

    # Test setting all levels of a municipality sets council_types to None, which
    # is an implied all. This will imply monitoring new councils as they are added to
    # the scraper.
    set_subscription_council_types(
        subscription,
        [
            _Form(name="byggingarfulltrui"),
            _Form(name="skipulagsfulltrui"),
            _Form(name="skipulagsrad"),
        ],
    )

    assert subscription.active
    assert subscription.council_types is None

    set_subscription_council_types(
        subscription,
        [
            _Form(name="byggingarfulltrui"),
        ],
    )

    # Setting to an empty list is unchecking the last option, this is an implied
    # deactivation, and not a removal.
    set_subscription_council_types(
        subscription,
        [],
    )

    assert subscription.council_types == [CouncilTypeEnum.byggingarfulltrui]
    assert not subscription.active

    # Test that subscription with no derived municipality, set the same three
    # councils as above, but this time do not set `council_types` back to `None`

    subscription.active = True
    subscription.type = SubscriptionTypeEnum.entity

    set_subscription_council_types(
        subscription,
        [
            _Form(name="byggingarfulltrui"),
            _Form(name="skipulagsfulltrui"),
            _Form(name="skipulagsrad"),
        ],
    )
    assert subscription.active
    assert not subscription.get_municipality()
    assert len(subscription.council_types) == 3
