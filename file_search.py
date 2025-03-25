import requests
import asyncio
from io import BytesIO
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI()

### Function to Create File
def create_file(client, file_path):
    """Creates a file in OpenAI using the provided path."""
    if file_path.startswith("http://") or file_path.startswith("https://"):
        # Download the file content from the URL
        response = requests.get(file_path)
        file_content = BytesIO(response.content)
        file_name = file_path.split("/")[-1]
        file_tuple = (file_name, file_content)
        result = client.files.create(
            file=file_tuple,
            purpose="assistants"
        )
    else:
        # Handle local file path
        with open(file_path, "rb") as file_content:
            result = client.files.create(
                file=file_content,
                purpose="assistants"
            )
    print(result.id)
    return result.id

### Function to Create Vector Store
async def create_vector_store(client, name="knowledge_base"):
    """Creates a vector store if it does not already exist."""
    try:
        # Check if vector store already exists
        vector_stores = client.vector_stores.list()
        for store in vector_stores:
            if store.name == name:
                print(f"Vector store '{name}' already exists.")
                return store
    except Exception as e:
        print(f"Error checking vector stores: {e}")

    # Create vector store if it does not exist
    try:
        vector_store = client.vector_stores.create(name=name)
        print(f"Created vector store: {vector_store.id}")
        return vector_store
    except Exception as e:
        print(f"Error creating vector store: {e}")
        return None

### Function to Check if File Exists in Vector Store
async def check_file_in_vector_store(client, vector_store_id, file_id):
    """Checks if the file already exists in the vector store."""
    try:
        files = client.vector_stores.files.list(vector_store_id=vector_store_id)
        for file in files:
            if file.id == file_id:  # Corrected attribute access
                print(f"File with ID {file_id} already exists in the vector store.")
                return True
    except Exception as e:
        print(f"Error checking files in vector store: {e}")
    return False

### Function to Populate Vector Store
async def populate_vector_store(client, vector_store_id, file_id):
    """Populates the vector store with the given file if it does not already exist."""
    if await check_file_in_vector_store(client, vector_store_id, file_id):
        print(f"Skipping adding file {file_id} as it already exists.")
        return

    try:
        client.vector_stores.files.create(
            vector_store_id=vector_store_id,
            file_id=file_id
        )
        print(f"Populated vector store with file ID: {file_id}")
    except Exception as e:
        print(f"Error populating vector store: {e}")

### Function to Check Vector Store Status
async def check_vector_store_status(client, vector_store_id, file_id):
    """Checks the status of the vector store until the file is complete."""
    while True:
        try:
            files = client.vector_stores.files.list(vector_store_id=vector_store_id)
            for file in files:
                if file.id == file_id:  # Corrected attribute access
                    if file.status == "completed":
                        print(f"File {file_id} status: Complete")
                        print(files)
                        return
                    else:
                        print(f"File {file_id} status: {file.status}. Waiting...")
            print("File not found in vector store. Waiting...")
        except Exception as e:
            print(f"Error checking vector store status: {e}")
        await asyncio.sleep(10)  # Wait for 10 seconds before checking again

### Main Function
async def main():
    ### Customize with your file path
    file_path = "https://icpkbtest.blob.core.windows.net/public-pdfs-bloblevel/testPDF2.pdf"
    file_id = create_file(client, file_path)
    
    vector_store = await create_vector_store(client)
    if vector_store:
        vector_store_id = vector_store.id
        await populate_vector_store(client, vector_store_id, file_id)
        await check_vector_store_status(client, vector_store_id, file_id)

    response = client.responses.create(
    model="gpt-4o-mini",
    input="How many files are in the vector store, and what are the contents of each file?",
    tools=[{
        "type": "file_search",
        "vector_store_ids": [vector_store.id]
    }],
    )
    output_text = None
    for output in response.output:
        if output.type == 'message':
            for content in output.content:
                if content.type == 'output_text':
                    output_text = content.text
                    break

    if output_text:
        print(output_text)
    else:
        print("No output text found in the response.")

if __name__ == "__main__":
    asyncio.run(main())
