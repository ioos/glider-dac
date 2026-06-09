from sqlalchemy import event
from glider_dac.models.deployment import Deployment
from glider_dac.extensions import db


@event.listens_for(db.session, "after_commit")
def after_commit(session):
    for obj in session.new.union(session.dirty):
        if isinstance(obj, Deployment):
            obj.save()
    for obj in session.deleted:
        if isinstance(obj, Deployment):
            obj.delete()
