compilemessages:
	python manage.py compilemessages

isort:
	isort -rc main/ dicpick/

nuke_db:
	python -m materiality.util.nuke_db
