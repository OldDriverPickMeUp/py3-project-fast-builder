# PY36-PROJECT-FAST-BUILDER


This project is used to have fast build of python3 project using docker.

## DEPENDENCE

python3
click
jinja2

## BEFORE START

You need to install python3.6 first.
It's better to install python3.6 with pyenv 

```
$ pyenv install 3.6.1
$ pyenv global 3.6.1
```

## BASIC USAGE

You can build your basic docker file by:
```
$ python manage.py [OPTIONS] COMMAND [ARGS]

```
There are some basic usage below.



### STEP 1 -- copy files and build your project env

copy this project into your project
```
$ mkdir your-project
$ cp -r some-folder/py36-project-fast-builder/* your-project
$ cd you-project
$ python -m venv venv
```
Activite virtualenv
```
$ . venv/bin/activite
```

### SETP 2 -- build docker and other basic files


Build docker with postgres and redis

```
$ python manage.py docker-gen --postgres --redis
```
Build .gitignore and .python-verision
```
$ python manage.py build-utils
```

## ADVANCED

There are some advanced usage below.

### AUTO BUILD README.md

There will be a file named tasks.json in project root folder to record all the tasks you have.
By typing this command:
```
$ python manage.py update-readme
```
A README.md file will be generated in your project root folder.
The readme templates is in code_templates/utils/README.md.j2.
You can easily custom it.

In the beginning, there will be no tasks. So,you should add some tasks.
```
$ python manage.py add-task PYTHON_FILE_PATH
```
This PYTHON_FILE_PATH will be a relative path from the project root folder.
Then this task will have a SERVICE_NAME generated from the path of the .py file.

You can also remove a task from the existing tasks.
```
$ python manage.py rm-task PYTHON_FILE_PATH
```

Both add-task and rm-task will cause an update of README.md

After we have all tasks,it is easier to generate the docker-compose.yml file

### SHOW ALL TASKS

```
$ python manage.py tasks
```

### START YOUR TASK FROM PROJECT ROOT FOLDER

You can make your task running naturally from your project's root folder without append anything to sys.path by using the below command.
```
$ python manage.py start --log-dir=/var/log/project_name RELATIVE_PY_FILENAME
```
RELATIVE_PY_FILENAME is relative path from the project root folder to the python file you'd like to run.

The manage.py start command will find the python file and import it.Trying to run the start_script() from you python file.

And the command will try start_service(), startup(), start() as the entry point of the task python file.

--log-dir is the log-file root path of this task.

### GENERATE DOCKER-COMPOSE SERVICE

Use below command you can generate docker-compse for each task.
```
$ python manage.py docker-compose-gen --dev FILENAME
```
This command will generate the service yaml code of this python file

You can custom the template in code_templates/docker-compose/service.j2.

### LOGGING
If you are using logging module,you must use log.logger as your log.
```
from log import logger
```

If you are using print() as a log, everything will be okay.
 
# GET HELP

```
$ python manage.py --help
```
```
$ python manage.py command --help
```



