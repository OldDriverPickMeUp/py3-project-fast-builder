import importlib
import json
import logging
from logging.handlers import RotatingFileHandler

import click
import os

import sys

from jinja2 import Environment, FileSystemLoader


def get_project_name():
    return os.path.basename(os.path.dirname(os.path.abspath(__file__)))


def get_logger_file_name(base_log_path, task_name):
    return os.path.join(base_log_path, task_name + '-stdout.log'), os.path.join(base_log_path,
                                                                                task_name + '-stderr.log')


def get_module_name(filename):
    file_path, _ = filename.split('.')
    return file_path.replace(os.path.sep, '.')


def get_service_name(module_name):
    return module_name.replace('.', '-')


JINJA_ENV = Environment(loader=FileSystemLoader(os.path.dirname(os.path.abspath(__file__))))


class NoErrorFilter(logging.Filter):
    def filter(self, record):
        return record.levelno < logging.ERROR


def config_logging(stdout_file, stderr_file):
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')
    max_bytes = 2 ** 10 * 10
    stdout_handler = RotatingFileHandler(stdout_file, maxBytes=max_bytes, backupCount=100)
    stdout_handler.addFilter(NoErrorFilter())
    stderr_handler = RotatingFileHandler(stderr_file, maxBytes=max_bytes, backupCount=100)
    stderr_handler.setLevel('ERROR')
    console_handler = logging.StreamHandler(sys.stdout)
    logging.basicConfig(format='[%(levelname)1.1s %(asctime)s %(module)s:%(lineno)d] %(message)s',
                        datefmt='%Y%m%d-%H:%M:%S', handlers=[stdout_handler, console_handler, stderr_handler],
                        level=LOG_LEVEL)


def log_exception(typ, value, tb):
    logging.error("Uncaught exception %s\n%r", exc_info=(typ, value, tb))


@click.group()
def cli():
    pass


@cli.command()
@click.argument('filename', type=click.Path(exists=True))
@click.option('--log-dir', default='.log', help='log file base folder')
def start(filename, log_dir):
    if not filename.endswith('.py'):
        click.echo('error input filename: {}'.format(filename))
        return

    module_name = get_module_name(filename)
    service_name = get_service_name(module_name)
    module = importlib.import_module(module_name)
    start_names = ['start_script', 'start_service', 'startup', 'start']
    for each_name in start_names:
        start_func = getattr(module, each_name, None)
        if callable(start_func):
            if not os.path.exists(log_dir):
                os.mkdir(log_dir)
            config_logging(*get_logger_file_name(log_dir, service_name))
            try:
                start_func()
            except Exception:
                log_exception(*sys.exc_info())
            break
    else:
        click.echo('can not find any start function {} in {}'.format(start_names, filename))


@cli.command('init')
@click.option('-f', '--force', is_flag=True, help='do initialization anyway')
@click.option('--redis', is_flag=True, help='add redis to package info')
@click.option('--postgres', is_flag=True, help='add postgres to package info')
def init(force, redis, postgres):
    pkg_info = PackageInfo()
    if pkg_info.inited() and force is not True:
        click.echo('project {} already inited, want to init again add -f/--force option'.format(get_project_name()))
        return
    if not os.path.exists(os.path.join(os.getcwd(), 'docker')):
        os.mkdir('docker')
    if redis:
        pkg_info.add_database('redis')
    if postgres:
        pkg_info.add_database('postgres')
    if not pkg_info.inited():
        pkg_info.save_pkg()

    need_files = ['dev.env', 'docker-compose.yml', 'Dockerfile']
    for each_template in need_files:
        template_path = os.path.sep.join(['code_templates', 'docker', each_template + '.j2'])
        out_file_path = os.path.sep.join(['docker', each_template])
        with open(out_file_path, 'w') as f:
            f.write(pkg_info.render_template(template_path, dev=True))
            click.echo('{} built'.format(out_file_path))

    need_files = ['.gitignore', '.python-version']
    for each_template in need_files:
        out_file_path = each_template
        template_path = os.path.sep.join(['code_templates', 'utils', each_template + '.j2'])
        if not os.path.exists(template_path):
            click.echo('template {} does not exist'.format(template_path))
            return
        template = JINJA_ENV.get_template(template_path)
        with open(out_file_path, 'w') as f:
            f.write(template.render())
            click.echo('{} built'.format(out_file_path))


@cli.command('docker-compose-service')
@click.argument('filename', type=click.Path(exists=True))
@click.option('--dev/--prod', default=True)
def docker_compose_service(filename, dev):
    if not filename.endswith('.py'):
        click.echo('error input filename: {}'.format(filename))
        return

    module_name = get_module_name(filename)
    service_name = get_service_name(module_name)
    template_path = os.path.sep.join(['code_templates', 'docker-compose', 'service.j2'])
    project_name = get_project_name()
    if not os.path.exists(template_path):
        click.echo('template {} does not exist'.format(template_path))
        return
    template = JINJA_ENV.get_template(template_path)
    click.echo(template.render(service_name=service_name, filename=filename, dev=dev,
                               project_name=project_name))


@cli.command('build-docker-compose')
@click.option('--dev/--prod', default=True, help='default in develop mode, add --prod to use product mode')
def build_docker_compose(dev):
    pkg_info = PackageInfo()
    click.echo(pkg_info.render_template('code_templates/docker/docker-compose.yml.j2', dev=dev))


class PackageInfo:
    _filename = 'package.json'

    def __init__(self):
        self._pkg_data = self.load_pkg_file()

    @staticmethod
    def init_pkg():
        return {
            'tasks': {},
            'databases': {},
            'inited': False
        }

    @classmethod
    def load_pkg_file(cls):
        if not os.path.exists(cls._filename):
            return cls.init_pkg()
        else:
            f = open(cls._filename)
            pkg_data = json.load(f)
            f.close()
            return pkg_data

    def save_pkg(self):
        self._pkg_data['inited'] = True
        with open(self._filename, 'w') as f:
            json.dump(self._pkg_data, f, indent=4)

    def inited(self):
        return self._pkg_data['inited']

    def get_tasks(self):
        return self._pkg_data['tasks']

    def get_databases(self):
        return self._pkg_data['databases']

    def add_task(self, filename):
        tasks = self.get_tasks()
        service_name = get_service_name(get_module_name(filename))
        task = tasks.get(service_name)
        if task:
            return '{} -- {} already exists'.format(service_name, filename)
        tasks[service_name] = filename
        self.save_pkg()
        return 'add task: {} -- {}'.format(service_name, filename)

    def iter_tasks(self):
        tasks = self.get_tasks()
        for service, file in tasks.items():
            yield '{} -- {}'.format(service, file)

    def remove_task(self, filename):
        service_name = get_service_name(get_module_name(filename))
        tasks = self.get_tasks()
        if tasks.get(service_name):
            del tasks[service_name]
            self.save_pkg()
            return 'removed: {} for {}'.format(service_name, filename)
        else:
            return 'can not find task {} for {}'.format(service_name, filename)

    @staticmethod
    def has_database_type(database_type):
        if database_type in ['postgres', 'redis']:
            return True
        return False

    def add_database(self, database_type):
        databases = self.get_databases()
        if self.has_database_type(database_type):
            if database_type in databases.keys():
                return 'already have database {}'.format(database_type)
            databases[database_type] = True
            self.save_pkg()
            return 'add database {}'.format(database_type)
        return 'don\'t support database {}'.format(database_type)

    def remove_database(self, database_type):
        databases = self.get_databases()
        if self.has_database_type(database_type):
            if database_type not in databases.keys():
                return 'there is no {} database'.format(database_type)
            databases[database_type] = False
            self.save_pkg()
            return 'removed: database {}'.format(database_type)
        return 'don\'t support database {}'.format(database_type)

    def iter_databases(self):
        databases = self.get_databases()
        for database_type in databases.keys():
            yield database_type

    def render_template(self, template_path, **kwargs):
        if not os.path.exists(template_path):
            return 'can not find README.md template {}'.format(template_path)
        template = JINJA_ENV.get_template(template_path)
        return template.render(tasks=self.get_tasks(),
                               project_name=get_project_name(),
                               **self.get_databases(), **kwargs)


@cli.command('add-task')
@click.argument('filename', type=click.Path(exists=True))
def add_task(filename):
    if not filename.endswith('.py'):
        click.echo('error input filename: {}'.format(filename))
        return
    pkg_info = PackageInfo()
    click.echo(pkg_info.add_task(filename))


@cli.command('rm-task')
@click.argument('filename', type=click.Path(exists=True))
def rm_task(filename):
    if not filename.endswith('.py'):
        click.echo('error input filename: {}'.format(filename))
        return
    pkg_info = PackageInfo()
    click.echo(pkg_info.remove_task(filename))


@cli.command('add-database')
@click.argument('database_type')
def add_database(database_type):
    pkg_info = PackageInfo()
    click.echo(pkg_info.add_database(database_type))


@cli.command('rm-database')
@click.argument('database_type')
def rm_database(database_type):
    pkg_info = PackageInfo()
    click.echo(pkg_info.remove_database(database_type))


@cli.command('tasks')
def tasks():
    pkg_info = PackageInfo()
    for task in pkg_info.iter_tasks():
        click.echo(task)


@cli.command('databases')
def databases():
    pkg_info = PackageInfo()
    for database in pkg_info.iter_databases():
        click.echo(database)


@cli.command('readme')
def readme():
    pkg_info = PackageInfo()
    click.echo(pkg_info.render_template('code_templates/utils/README.md.j2'))


if __name__ == '__main__':
    cli()
