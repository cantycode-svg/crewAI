import json
import logging
import os
import pickle
from datetime import datetime
from typing import Any, TypedDict

from supabase import Client, create_client
from typing_extensions import Unpack

from crewai.utilities.errors import DatabaseError, DatabaseOperationError

logger = logging.getLogger(__name__)


class LogEntry(TypedDict, total=False):
    """TypedDict for log entry kwargs with optional fields for flexibility."""

    task_name: str
    task: str
    agent: str
    status: str
    output: str
    input: str
    message: str
    level: str
    crew: str
    flow: str
    tool: str
    error: str
    duration: float
    metadata: dict[str, Any]


class FileHandler:
    """Handler for logging operations using Supabase-based storage.

    All log entries are written to the 'logs' table in Supabase.
    Local file operations are bypassed in favor of cloud storage.

    Attributes:
        client: Supabase client instance.
        supabase_url: Supabase project URL.
        supabase_key: Supabase project API key.
    """

    def __init__(self, file_path: bool | str | None = None) -> None:
        """Initialize the FileHandler with Supabase connection.

        Args:
            file_path: Ignored parameter for backward compatibility.
                      All logging now goes to Supabase.

        Raises:
            DatabaseOperationError: If connection parameters are missing or initialization fails.
        """
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")

        if not self.supabase_url or not self.supabase_key:
            error_msg = "Supabase URL and Key must be provided as environment variables (SUPABASE_URL, SUPABASE_KEY)"
            logger.error(error_msg)
            raise DatabaseOperationError(error_msg, None)

        try:
            self.client: Client = create_client(self.supabase_url, self.supabase_key)
            self._verify_table_access()
        except Exception as e:
            error_msg = DatabaseError.format_error(DatabaseError.INIT_ERROR, e)
            logger.error(error_msg)
            raise DatabaseOperationError(error_msg, e) from e

    def _verify_table_access(self) -> None:
        """Verify that the 'logs' table exists and is accessible in Supabase.

        Note: The 'logs' table should be created in Supabase with the following schema:

        logs table:
        - id (uuid, primary key, default: gen_random_uuid())
        - timestamp (timestamp with time zone, default: now())
        - task_name (text, nullable)
        - task (text, nullable)
        - agent (text, nullable)
        - status (text, nullable)
        - output (text, nullable)
        - input (text, nullable)
        - message (text, nullable)
        - level (text, nullable)
        - crew (text, nullable)
        - flow (text, nullable)
        - tool (text, nullable)
        - error (text, nullable)
        - duration (double precision, nullable)
        - metadata (jsonb, nullable)

        Raises:
            DatabaseOperationError: If table cannot be accessed.
        """
        try:
            self.client.table("logs").select("id").limit(1).execute()
            logger.info("Successfully connected to Supabase and verified 'logs' table access")
        except Exception as e:
            error_msg = f"Failed to verify Supabase 'logs' table: {str(e)}"
            logger.error(error_msg)
            raise DatabaseOperationError(error_msg, e) from e

    def log(self, **kwargs: Unpack[LogEntry]) -> None:
        """Log data with structured fields to Supabase 'logs' table.

        Keyword Args:
            task_name: Name of the task.
            task: Description of the task.
            agent: Name of the agent.
            status: Status of the operation.
            output: Output data.
            input: Input data.
            message: Log message.
            level: Log level (e.g., INFO, ERROR).
            crew: Name of the crew.
            flow: Name of the flow.
            tool: Name of the tool used.
            error: Error message if any.
            duration: Duration of the operation in seconds.
            metadata: Additional metadata as a dictionary.

        Raises:
            DatabaseOperationError: If logging fails.
        """
        try:
            now = datetime.now().isoformat()
            log_entry = {"timestamp": now, **kwargs}

            # Convert metadata to JSON if present
            if "metadata" in log_entry and isinstance(log_entry["metadata"], dict):
                log_entry["metadata"] = json.loads(
                    json.dumps(log_entry["metadata"])
                )

            response = self.client.table("logs").insert(log_entry).execute()

            if not response.data:
                raise DatabaseOperationError(
                    "Failed to insert log entry - no data returned", None
                )

            logger.debug(f"Successfully logged entry to Supabase: {log_entry.get('message', 'No message')}")

        except Exception as e:
            error_msg = DatabaseError.format_error(DatabaseError.SAVE_ERROR, e)
            logger.error(error_msg)
            raise DatabaseOperationError(error_msg, e) from e


class PickleHandler:
    """Handler for saving and loading data using pickle.

    Note: This class maintains local file operations for backward compatibility.
    Consider migrating to Supabase-based storage for production use.

    Attributes:
        file_path: The path to the pickle file.
    """

    def __init__(self, file_name: str) -> None:
        """Initialize the PickleHandler with the name of the file where data will be stored.

        The file will be saved in the current directory.

        Args:
            file_name: The name of the file for saving and loading data.
        """
        if not file_name.endswith(".pkl"):
            file_name += ".pkl"
        self.file_path = os.path.join(os.getcwd(), file_name)

    def initialize_file(self) -> None:
        """Initialize the file with an empty dictionary and overwrite any existing data."""
        self.save({})

    def save(self, data: Any) -> None:
        """Save the data to the specified file using pickle.

        Args:
          data: The data to be saved to the file.
        """
        with open(self.file_path, "wb") as f:
            pickle.dump(obj=data, file=f)

    def load(self) -> Any:
        """Load the data from the specified file using pickle.

        Returns:
            The data loaded from the file.
        """
        if not os.path.exists(self.file_path) or os.path.getsize(self.file_path) == 0:
            return {}  # Return an empty dictionary if the file does not exist or is empty

        with open(self.file_path, "rb") as file:
            try:
                return pickle.load(file)  # noqa: S301
            except EOFError:
                return {}  # Return an empty dictionary if the file is empty or corrupted
            except Exception:
                raise  # Raise any other exceptions that occur during loading
