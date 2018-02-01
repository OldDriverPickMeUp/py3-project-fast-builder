# PY36-PROJECT-FAST-BUILDER


This project is used to have fast build of python3 project using docker.

## DEPENDENCE

python3
click
jinja2
```
$ pip install click jinja2
```

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

Copy manage.py and code_templates into your project
```
$ mkdir your-project
$ cp some-folder/py36-project-fast-builder/manage.py your-project
$ cp -r some-folder/py36-project-fast-builder/code_templates your-project
$ cd you-project
$ python -m venv venv
```
Activite virtualenv
```
$ . venv/bin/activite
```

### SETP 2 -- Initialize the develop environment


This will build development environment docker file including docker/dev.env docker/docker-compose.yml docker/Dockerfile.

.python-version and .gitingore will be built in the base project folder.
```
$ python manage.py init --postgres --redis
```
Option --postgres will add postgresql for docker-compose.yml and dev.env.

Option --redis will add redis for docker-compose.yml and dev.env.

will add --nginx soon.

## ADVANCED

There are some advanced usage below.

### AUTO BUILD README.md

There will be a file named package.json in project root folder to record all the tasks you have.
By typing this command:
```
$ python manage.py readme > your_README.md
```
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
```
$ python manage.py build-docker-compose --postgres --redis --dev > docker/docker-compose.yml
```

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
$ python manage.py docker-compose-service --dev FILENAME
```
This command will generate the service yaml code of this python file

You can custom the template in code_templates/docker-compose/service.j2.

### LOGGING
If you start your task by
```
$ python manage.py start --log-dir=/var/log task3.py
```
`/var/log/project_name/task3-stdout.log` and `/var/log/project_name/task3-stderr.log` will be built to record all records maded from python logging module.

In stdout log file, log level defined in your environment variable will be used.
And the stdout log file will not record log level above logging.WARNING.

In stderr log file, all log records with level higher than warning will be recorded.
And all uncaught Exception will be logged into this file as well.
 
## GET HELP

```
$ python manage.py --help
```
```
$ python manage.py command --help
```

## ALL COMMANDS

### add-task

Add a task to package.json, will be used to generate docker-compose.yml and readme.
```
Usage: manage.py add-task FILENAME
```
FILENAME is a .py file where your task entry point in, just like `test/task2.py`

### build-docker-compose
Echo your docker-compose.yml built from the current package.json.
So you can replace your current docker-compose.yml.

### docker-compose-service
Echo a single docker-compose.yml service is built from a .py file
 
### init
Initialize your project.

### readme
Echo a README is built from current package.json

### rm-task
Remove a task from package.json
### start
Start a task from a .py file

### tasks
Show all tasks in package.json

### add-database
Add a database for this project
```
Usage: manage.py add-database DATABASE_TYPE
```
### rm-database
Remove database for this project

### databases
Show all database in package.json




