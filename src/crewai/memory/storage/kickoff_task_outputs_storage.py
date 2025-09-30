import json
import logging
import os
from typing import Any
from supabase import create_client, Client
from crewai.task import Task
from crewai.utilities import Printer
from crewai.utilities.crew_json_encoder import CrewJSONEncoder
from crewai.utilities.errors import DatabaseError, DatabaseOperationError

logger = logging.getLogger(__name__)


class KickoffTaskOutputsSupabaseStorage:
    """
    A Supabase storage class for kickoff task outputs storage.
    Uses environment variables for connection and stores data in 'results' and 'crew_state' tables.
    """

    def __init__(self, supabase_url: str | None = None, supabase_key: str | None = None) -> None:
        """
        Initialize the Supabase storage client.
        
        Args:
            supabase_url: Supabase project URL. If None, reads from SUPABASE_URL env variable.
            supabase_key: Supabase project API key. If None, reads from SUPABASE_KEY env variable.
        
        Raises:
            DatabaseOperationError: If connection parameters are missing or initialization fails.
        """
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            error_msg = "Supabase URL and Key must be provided either as parameters or environment variables (SUPABASE_URL, SUPABASE_KEY)"
            logger.error(error_msg)
            raise DatabaseOperationError(error_msg, None)
        
        self._printer: Printer = Printer()
        
        try:
            self.client: Client = create_client(self.supabase_url, self.supabase_key)
            self._initialize_tables()
        except Exception as e:
            error_msg = DatabaseError.format_error(DatabaseError.INIT_ERROR, e)
            logger.error(error_msg)
            raise DatabaseOperationError(error_msg, e) from e

    def _initialize_tables(self) -> None:
        """
        Verify that required tables exist in Supabase.
        
        Note: Tables should be created in Supabase with the following schemas:
        
        results table:
        - task_id (text, primary key)
        - expected_output (text)
        - output (jsonb)
        - task_index (integer)
        - inputs (jsonb)
        - was_replayed (boolean)
        - timestamp (timestamp with time zone, default: now())
        
        crew_state table:
        - id (uuid, primary key, default: gen_random_uuid())
        - task_id (text)
        - state_data (jsonb)
        - timestamp (timestamp with time zone, default: now())
        
        This method performs a simple query to check table accessibility.
        
        Raises:
            DatabaseOperationError: If tables cannot be accessed.
        """
        try:
            # Check if results table exists and is accessible
            self.client.table("results").select("task_id").limit(1).execute()
            # Check if crew_state table exists and is accessible
            self.client.table("crew_state").select("id").limit(1).execute()
            logger.info("Successfully connected to Supabase and verified table access")
        except Exception as e:
            error_msg = f"Failed to verify Supabase tables: {str(e)}"
            logger.error(error_msg)
            raise DatabaseOperationError(error_msg, e) from e

    def add(
        self,
        task: Task,
        output: dict[str, Any],
        task_index: int,
        was_replayed: bool = False,
        inputs: dict[str, Any] | None = None,
    ) -> None:
        """
        Add a new task output record to the results table.
        
        Args:
            task: The Task object containing task details.
            output: Dictionary containing the task's output data.
            task_index: Integer index of the task in the sequence.
            was_replayed: Boolean indicating if this was a replay execution.
            inputs: Dictionary of input parameters used for the task.
        
        Raises:
            DatabaseOperationError: If saving the task output fails.
        """
        inputs = inputs or {}
        
        try:
            # Serialize output and inputs to JSON strings
            output_json = json.loads(json.dumps(output, cls=CrewJSONEncoder))
            inputs_json = json.loads(json.dumps(inputs, cls=CrewJSONEncoder))
            
            data = {
                "task_id": str(task.id),
                "expected_output": task.expected_output,
                "output": output_json,
                "task_index": task_index,
                "inputs": inputs_json,
                "was_replayed": was_replayed,
            }
            
            # Use upsert to insert or update if task_id already exists
            response = self.client.table("results").upsert(data).execute()
            
            if not response.data:
                raise DatabaseOperationError("Failed to insert task output - no data returned", None)
                
            logger.info(f"Successfully added task output for task_id: {task.id}")
            
        except Exception as e:
            error_msg = DatabaseError.format_error(DatabaseError.SAVE_ERROR, e)
            logger.error(error_msg)
            raise DatabaseOperationError(error_msg, e) from e

    def update(
        self,
        task_index: int,
        **kwargs: Any,
    ) -> None:
        """
        Update an existing task output record in the results table.
        
        Updates fields of a task output record identified by task_index. The fields
        to update are provided as keyword arguments.
        
        Args:
            task_index: Integer index of the task to update.
            **kwargs: Arbitrary keyword arguments representing fields to update.
                     Values that are dictionaries will be JSON encoded.
        
        Raises:
            DatabaseOperationError: If updating the task output fails.
        """
        try:
            # Prepare update data
            update_data = {}
            for key, value in kwargs.items():
                if isinstance(value, dict):
                    update_data[key] = json.loads(json.dumps(value, cls=CrewJSONEncoder))
                else:
                    update_data[key] = value
            
            # Update record by task_index
            response = self.client.table("results").update(update_data).eq("task_index", task_index).execute()
            
            if not response.data:
                logger.warning(f"No row found with task_index {task_index}. No update performed.")
            else:
                logger.info(f"Successfully updated task output for task_index: {task_index}")
                
        except Exception as e:
            error_msg = DatabaseError.format_error(DatabaseError.UPDATE_ERROR, e)
            logger.error(error_msg)
            raise DatabaseOperationError(error_msg, e) from e

    def load(self) -> list[dict[str, Any]]:
        """
        Load all task output records from the results table.
        
        Returns:
            List of dictionaries containing task output records, ordered by task_index.
            Each dictionary contains: task_id, expected_output, output, task_index,
            inputs, was_replayed, and timestamp.
        
        Raises:
            DatabaseOperationError: If loading task outputs fails.
        """
        try:
            response = self.client.table("results").select("*").order("task_index").execute()
            
            results = []
            for row in response.data:
                result = {
                    "task_id": row.get("task_id"),
                    "expected_output": row.get("expected_output"),
                    "output": row.get("output"),
                    "task_index": row.get("task_index"),
                    "inputs": row.get("inputs"),
                    "was_replayed": row.get("was_replayed"),
                    "timestamp": row.get("timestamp"),
                }
                results.append(result)
            
            logger.info(f"Successfully loaded {len(results)} task output records")
            return results
            
        except Exception as e:
            error_msg = DatabaseError.format_error(DatabaseError.LOAD_ERROR, e)
            logger.error(error_msg)
            raise DatabaseOperationError(error_msg, e) from e

    def delete_all(self) -> None:
        """
        Delete all task output records from the results table.
        
        This method removes all records from the results table.
        Use with caution as this operation cannot be undone.
        
        Raises:
            DatabaseOperationError: If deleting task outputs fails.
        """
        try:
            # Delete all records from results table
            response = self.client.table("results").delete().neq("task_id", "").execute()
            
            logger.info("Successfully deleted all task output records from results table")
            
        except Exception as e:
            error_msg = DatabaseError.format_error(DatabaseError.DELETE_ERROR, e)
            logger.error(error_msg)
            raise DatabaseOperationError(error_msg, e) from e

    def save_crew_state(
        self,
        task_id: str,
        state_data: dict[str, Any],
    ) -> None:
        """
        Save crew state data to the crew_state table.
        
        Args:
            task_id: The task ID associated with this state.
            state_data: Dictionary containing the crew state data.
        
        Raises:
            DatabaseOperationError: If saving crew state fails.
        """
        try:
            state_json = json.loads(json.dumps(state_data, cls=CrewJSONEncoder))
            
            data = {
                "task_id": task_id,
                "state_data": state_json,
            }
            
            response = self.client.table("crew_state").insert(data).execute()
            
            if not response.data:
                raise DatabaseOperationError("Failed to insert crew state - no data returned", None)
            
            logger.info(f"Successfully saved crew state for task_id: {task_id}")
            
        except Exception as e:
            error_msg = f"Failed to save crew state: {str(e)}"
            logger.error(error_msg)
            raise DatabaseOperationError(error_msg, e) from e

    def load_crew_state(self, task_id: str | None = None) -> list[dict[str, Any]]:
        """
        Load crew state data from the crew_state table.
        
        Args:
            task_id: Optional task ID to filter by. If None, loads all states.
        
        Returns:
            List of dictionaries containing crew state records.
        
        Raises:
            DatabaseOperationError: If loading crew state fails.
        """
        try:
            query = self.client.table("crew_state").select("*").order("timestamp")
            
            if task_id:
                query = query.eq("task_id", task_id)
            
            response = query.execute()
            
            logger.info(f"Successfully loaded {len(response.data)} crew state records")
            return response.data
            
        except Exception as e:
            error_msg = f"Failed to load crew state: {str(e)}"
            logger.error(error_msg)
            raise DatabaseOperationError(error_msg, e) from e

    def delete_crew_state(self, task_id: str | None = None) -> None:
        """
        Delete crew state records from the crew_state table.
        
        Args:
            task_id: Optional task ID to filter by. If None, deletes all states.
        
        Raises:
            DatabaseOperationError: If deleting crew state fails.
        """
        try:
            if task_id:
                response = self.client.table("crew_state").delete().eq("task_id", task_id).execute()
                logger.info(f"Successfully deleted crew state for task_id: {task_id}")
            else:
                response = self.client.table("crew_state").delete().neq("id", "").execute()
                logger.info("Successfully deleted all crew state records")
                
        except Exception as e:
            error_msg = f"Failed to delete crew state: {str(e)}"
            logger.error(error_msg)
            raise DatabaseOperationError(error_msg, e) from e
