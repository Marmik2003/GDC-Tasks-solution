from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

class TasksCommand:
    TASKS_FILE = "tasks.txt"
    COMPLETED_TASKS_FILE = "completed.txt"

    current_items = {}
    completed_items = []

    def read_current(self):
        try:
            file = open(self.TASKS_FILE, "r")
            for line in file.readlines():
                item = line[:-1].split(" ")
                self.current_items[int(item[0])] = " ".join(item[1:])
            file.close()
        except Exception:
            pass

    def read_completed(self):
        try:
            file = open(self.COMPLETED_TASKS_FILE, "r")
            self.completed_items = file.readlines()
            file.close()
        except Exception:
            pass

    def write_current(self):
        with open(self.TASKS_FILE, "w+") as f:
            f.truncate(0)
            for key in sorted(self.current_items.keys()):
                f.write(f"{key} {self.current_items[key]}\n")

    def write_completed(self):
        with open(self.COMPLETED_TASKS_FILE, "w+") as f:
            f.truncate(0)
            for item in self.completed_items:
                f.write(f"{item}\n")

    def runserver(self):
        address = "127.0.0.1"
        port = 8000
        server_address = (address, port)
        httpd = HTTPServer(server_address, TasksServer)
        print(f"Started HTTP Server on http://{address}:{port}")
        httpd.serve_forever()

    def run(self, command, args):
        self.read_current()
        self.read_completed()
        if command == "add":
            self.add(args)
        elif command == "done":
            self.done(args)
        elif command == "delete":
            self.delete(args)
        elif command == "ls":
            self.ls()
        elif command == "report":
            self.report()
        elif command == "runserver":
            self.runserver()
        elif command == "help":
            self.help()

    def help(self):
        print(
            """Usage :-
$ python tasks.py add 2 hello world # Add a new item with priority 2 and text "hello world" to the list
$ python tasks.py ls # Show incomplete priority list items sorted by priority in ascending order
$ python tasks.py del PRIORITY_NUMBER # Delete the incomplete item with the given priority number
$ python tasks.py done PRIORITY_NUMBER # Mark the incomplete item with the given PRIORITY_NUMBER as complete
$ python tasks.py help # Show usage
$ python tasks.py report # Statistics
$ python tasks.py runserver # Starts the tasks management server"""
        )

    def add(self, args):
        priority = int(args[0])
        text = " ".join(args[1:])

        priority2 = priority
        items = []
        if priority2 in sorted(self.current_items):
            while priority2 in sorted(self.current_items):
                items.append(priority2)
                priority2 += 1
        items.reverse()
        for item in items:
            self.current_items[item + 1] = self.current_items[item]

        self.current_items[priority] = text
        print(f'Added task: "{text}" with priority {priority}')
        self.write_current()
    def done(self, args):
        priority = int(args[0])
        try:
            self.completed_items.append(self.current_items[priority])
            del self.current_items[priority]
        except KeyError:
            print(f"Error: no incomplete item with priority {priority} exists.")
            return
        print("Marked item as done.")
        self.write_current()
        self.write_completed()

    def delete(self, args):
        priority = int(args[0])
        try:
            del self.current_items[priority]
        except KeyError:
            print(f"Error: item with priority {priority} does not exist. Nothing deleted.")
            return
        print(f"Deleted item with priority {priority}.")
        self.write_current()

    def ls(self):
        for i, key in enumerate(sorted(self.current_items.keys())):
            print(f"{i+1}. {self.current_items[key]} [{key}]")

    def report(self):
        print(f"Pending : {len(self.current_items)}")
        for i, key in enumerate(sorted(self.current_items.keys())):
            print(f"{i+1}. {self.current_items[key]} [{key}]")
        print(f"\nCompleted : {len(self.completed_items)}")
        for i, item in enumerate(self.completed_items):
            print(f"{i+1}. {item}")

    def render_pending_tasks(self):
        tasks = []
        for i, key in enumerate(sorted(self.current_items.keys())):
            tasks.append(f"{i+1}. {self.current_items[key]} [{key}]")
        if len(tasks) == 0:
            string = "<h1> No pending tasks </h1>"
        else:
            string = "<h1> Pending Tasks: </h1>\n<ul>\n"
            for task in tasks:
                string += f"<li>{task} - <a role='button' href='/done/{task.split('[')[1][:-1]}'>Done</a> &nbsp; <a role='button' href='/delete/{task.split('[')[1][:-1]}'>Delete</a> </li>\n"
            string += "</ul>"
        return string

    def render_completed_tasks(self):
        tasks = []
        for i, item in enumerate(self.completed_items):
            tasks.append(f"{i+1}. {item}")
        if len(tasks) == 0:
            string = "<h1> No completed tasks </h1>"
        else:
            string = "<h1> Completed Tasks: </h1>\n<ul>\n"
            for task in tasks:
                string += f"<li>{task}</li>\n"
            string += "</ul>"
        return string

    def render_add_task(self):
        string = """
<h1> Add Task </h1>
<form action="add" method="post">
<input type="number" name="priority" placeholder="Priority">
<input type="text" name="text" placeholder="Text">
<input type="submit" value="Add">
</form>"""
        return string


class TasksServer(TasksCommand, BaseHTTPRequestHandler):
    def do_GET(self):
        task_command_object = TasksCommand()
        if self.path == "/tasks":
            content = task_command_object.render_pending_tasks()
        elif self.path == "/completed":
            content = task_command_object.render_completed_tasks()
        elif self.path == "/add":
            content = task_command_object.render_add_task()
        elif self.path.startswith("/done"):
            task_command_object.done(self.path.split("/")[2:])
            content = task_command_object.render_pending_tasks()
        elif self.path.startswith("/delete"):
            task_command_object.delete(self.path.split("/")[2])
            content = task_command_object.render_pending_tasks()
        else:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("content-type", "text/html")
        self.end_headers()
        self.wfile.write(content.encode())

    def do_POST(self):
        task_command_object = TasksCommand()
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length).decode()
        post_data = parse_qs(post_data)
        if self.path == "/add":
            task_command_object.add(f'{post_data["priority"][0]} {post_data["text"][0]}'.split())
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"<h1> Task added </h1>")
