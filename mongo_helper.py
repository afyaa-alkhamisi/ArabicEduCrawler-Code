{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 1,
   "id": "bd712b4f",
   "metadata": {},
   "outputs": [],
   "source": [
    "# mongo_helper.ipynb\n",
    "import os\n",
    "import socket\n",
    "from pymongo import MongoClient\n",
    "from dotenv import load_dotenv\n",
    "\n",
    "load_dotenv()\n",
    "\n",
    "\n",
    "def is_running_in_docker() -> bool:\n",
    "    \"\"\"Detect if we are running inside a Docker container.\"\"\"\n",
    "    # This file exists only inside Docker containers\n",
    "    if os.path.exists(\"/.dockerenv\"):\n",
    "        return True\n",
    "    # Another fallback check\n",
    "    try:\n",
    "        with open(\"/proc/1/cgroup\", \"rt\") as f:\n",
    "            return \"docker\" in f.read() or \"containerd\" in f.read()\n",
    "    except Exception:\n",
    "        return False\n",
    "\n",
    "\n",
    "def get_mongo_client():\n",
    "    \"\"\"Return a ready-to-use MongoClient that works both inside and outside Docker.\"\"\"\n",
    "    mongo_user = os.getenv(\"MONGO_INITDB_ROOT_USERNAME\", \"mongoadmin\")\n",
    "    mongo_pass = os.getenv(\"MONGO_INITDB_ROOT_PASSWORD\", \"mongoadmin\")\n",
    "    mongo_db = os.getenv(\"MONGO_DB\", \"crawlDB\")\n",
    "    mongo_port = os.getenv(\"MONGO_PORT\", \"27017\")\n",
    "\n",
    "    if is_running_in_docker():\n",
    "        # Inside Docker → use service name + internal port\n",
    "        mongo_host = os.getenv(\"MONGO_CONTAINER\", \"mongo\")\n",
    "        print(\"🔹 Running inside Docker – connecting to\",\n",
    "              f\"{mongo_host}:{mongo_port}\")\n",
    "    else:\n",
    "        # On host machine → use localhost + mapped external port\n",
    "        mongo_host = \"localhost\"\n",
    "        mongo_port = \"27018\"\n",
    "        print(\"💻 Running on host – connecting to\",\n",
    "              f\"{mongo_host}:{mongo_port}\")\n",
    "\n",
    "    mongo_uri = (\n",
    "        f\"mongodb://{mongo_user}:{mongo_pass}@{mongo_host}:{mongo_port}/\"\n",
    "        f\"{mongo_db}?authSource=admin\"\n",
    "    )\n",
    "\n",
    "    client = MongoClient(\n",
    "        mongo_uri,\n",
    "        serverSelectionTimeoutMS=5000,  # 5 seconds\n",
    "        heartbeatFrequencyMS=10000\n",
    "    )\n",
    "    return client[mongo_db]"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "base",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.12.4"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
