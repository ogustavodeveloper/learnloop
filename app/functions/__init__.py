from azure.storage.blob import BlobServiceClient
import os 

def upload_arquivo(container_name, file_path, blob_name):
        try:
                # Obter a connection string dos segredos (variável de ambiente)
            connection_string = os.getenv('CONECTION')
            if not connection_string:
                raise ValueError("Connection string não encontrada nos segredos.")

                                                    # Conectar ao serviço Blob e ao container
            blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
                                                                            
                                                                                    
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
                                                                                                                
                                                                                                                    
            blob_url = blob_client.url
            return blob_url

        except Exception as e:
            print(f"Erro ao enviar o arquivo: {e}")
            return None




