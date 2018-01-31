import importlib
import json

import click
import os

import sys

from jinja2 import Environment, FileSystemLoader


def get_project_name():
    return os.path.basename(os.path.dirname(os.path.abspath(__file__)))


JINJA_ENV = Environment(loader=FileSystemLoader(os.path.dirname(os.path.abspath(__file__))))


@click.group()
def cli():
    pass


@cli.command()
@click.argument('filename', type=click.Path(exists=True))
@click.option('--log-dir', default='.log', help='log file base folder')
@click.option('--debug/--no-debug', default=False, help='whether in debug mode or not')
def start(filename, log_dir, debug):
    if not filename.endswith('.py'):
        click.echo('error input filename: {}'.format(filename))
        return

    module_name = get_module_name(filename)
    service_name = get_service_name(module_name)
    stdout_logger = _StdoutLogger(service_name, log_dir, debug=debug)
    stderr_logger = _StderrLogger(service_name, log_dir, debug=debug)
    stderr_logger.activate()
    stdout_logger.activate()
    module = importlib.import_module(module_name)
    start_names = ['start_script', 'start_service', 'startup', 'start']
    for each_name in start_names:
        start_func = getattr(module, each_name, None)
        if callable(start_func):
            start_func()
            break
    else:
        click.echo('can not find any start function {} in {}'.format(start_names, filename))
    stdout_logger.deactivate()
    stderr_logger.deactivate()


def get_module_name(filename):
    file_path, _ = filename.split('.')
    return file_path.replace(os.path.sep, '.')


def get_service_name(module_name):
    return module_name.replace('.', '-')


class _BaseOutStream:
    _stream_type = None

    def __init__(self, task_name, base_log_path, debug=False):
        self._check_exist_and_mk(base_log_path)
        self._debug = debug
        if self._debug:
            self.log_name = os.path.join(base_log_path, 'DEBUG-' + task_name + '-' + self._stream_type + '.log')
        else:
            self.log_name = os.path.join(base_log_path, task_name + '-' + self._stream_type + '.log')

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    @staticmethod
    def _check_exist_and_mk(path):
        dir_path = os.path.abspath(path)
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

    def flush(self):
        # this flush method is needed for python 3 compatibility.
        # this handles the flush command by doing nothing.
        # you might want to specify some extra behavior here.
        pass

    def activate(self):
        self.terminal = getattr(sys, self._stream_type)
        self.log = open(self.log_name, 'a')
        setattr(sys, self._stream_type, self)

    def deactivate(self):
        setattr(sys, self._stream_type, self.terminal)
        self.log.close()


class _StdoutLogger(_BaseOutStream):
    _stream_type = 'stdout'


class _StderrLogger(_BaseOutStream):
    _stream_type = 'stderr'


@cli.command('init')
@click.option('--postgres/--no-postgres', default=False)
@click.option('--redis/--no-redis', default=False)
def init(postgres, redis):
    if not os.path.exists(os.path.join(os.getcwd(), 'docker')):
        os.mkdir('docker')
    need_files = ['dev.env', 'docker-compose.yml', 'Dockerfile']
    render_data = {
        'project_name': get_project_name(),
        'dev': True,
        'postgres': postgres,
        'redis': redis
    }
    for each_template in need_files:
        template_path = os.path.sep.join(['code_templates', 'docker', each_template + '.j2'])
        out_file_path = os.path.sep.join(['docker', each_template])
        if not os.path.exists(template_path):
            click.echo('template {} does not exist'.format(template_path))
            return
        template = JINJA_ENV.get_template(template_path)
        with open(out_file_path, 'w') as f:
            f.write(template.render(**render_data))
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
    click.echo('template for {}'.format(filename))
    click.echo(template.render(service_name=service_name, filename=filename, dev=dev,
                               project_name=project_name))


@cli.command('build-docker-compose')
@click.option('--dev/--prod', default=True)
@click.option('--postgres/--no-postgres', default=False)
@click.option('--redis/--no-redis', default=False)
def build_docker_compose(dev, postgres, redis):
    need_files = ['docker-compose.yml']
    tasks = Tasks.get_tasks()
    render_data = {
        'project_name': get_project_name(),
        'dev': dev,
        'postgres': postgres,
        'redis': redis,
        'tasks': tasks
    }
    for each_template in need_files:
        template_path = os.path.sep.join(['code_templates', 'docker', each_template + '.j2'])
        if not os.path.exists(template_path):
            click.echo('template {} does not exist'.format(template_path))
            return
        template = JINJA_ENV.get_template(template_path)
        click.echo(template.render(**render_data))


class Tasks:
    _filename = 'tasks.json'
    _readme = 'README.md'
    _readme_template = os.path.sep.join(['code_templates', 'utils', _readme + '.j2'])

    @classmethod
    def check_and_build_task_file(cls):
        if not os.path.exists(cls._filename):
            with open(cls._filename, 'w') as f:
                json.dump({}, f)

    @classmethod
    def get_tasks(cls):
        cls.check_and_build_task_file()
        with open(cls._filename) as f:
            tasks = json.load(f)
        return tasks

    @classmethod
    def save_tasks(cls, tasks):
        with open(cls._filename, 'w') as f:
            json.dump(tasks, f)

    @classmethod
    def add_task(cls, filename):
        tasks = cls.get_tasks()
        service_name = get_service_name(get_module_name(filename))
        task = tasks.get(service_name)
        if task:
            click.echo('{} -- {} already exists'.format(service_name, filename))
            return
        tasks[service_name] = filename
        cls.save_tasks(tasks)
        click.echo('add task: {} -- {}'.format(service_name, filename))

    @classmethod
    def show_tasks(cls):
        tasks = cls.get_tasks()
        for service, file in tasks.items():
            click.echo('{} -- {}'.format(service, file))

    @classmethod
    def remove_task(cls, filename):
        service_name = get_service_name(get_module_name(filename))
        tasks = cls.get_tasks()
        if tasks.get(service_name):
            del tasks[service_name]
            cls.save_tasks(tasks)
            click.echo('removed: {} for {}'.format(service_name, filename))
        else:
            click.echo('can not find task {} for {}'.format(service_name, filename))

    @classmethod
    def readme(cls):
        tasks = cls.get_tasks()
        if not os.path.exists(cls._readme_template):
            click.echo('can not find README.md template {}'.format(cls._readme_template))
            return
        template = JINJA_ENV.get_template(cls._readme_template)
        click.echo(template.render(tasks=tasks.items(), project_name=get_project_name()))


@cli.command('add-task')
@click.argument('filename', type=click.Path(exists=True))
def add_task(filename):
    if not filename.endswith('.py'):
        click.echo('error input filename: {}'.format(filename))
        return
    Tasks.add_task(filename)


@cli.command('rm-task')
@click.argument('filename', type=click.Path(exists=True))
def rm_task(filename):
    if not filename.endswith('.py'):
        click.echo('error input filename: {}'.format(filename))
        return
    Tasks.remove_task(filename)


@cli.command('tasks')
def tasks():
    Tasks.show_tasks()


@cli.command('readme')
def readme():
    Tasks.readme()


if __name__ == '__main__':
    cli()
