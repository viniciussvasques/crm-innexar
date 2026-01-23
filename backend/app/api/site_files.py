import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.site_files import FileNode, FileContentResponse, FileSaveRequest
from typing import List
from pathlib import Path

router = APIRouter(prefix="/projects/{project_id}/files", tags=["site-files"])

# Base directory for generated sites
# In production this should be an env var
SITES_BASE_DIR = Path(os.getenv("SITES_BASE_DIR", "./generated_sites"))

def get_project_dir(project_id: int) -> Path:
    return SITES_BASE_DIR / f"project_{project_id}"

def validate_path(project_dir: Path, requested_path: str) -> Path:
    """
    Securely resolves and validates a file path preventing traversal attacks.
    """
    # Remove leading slashes to treat as relative
    clean_req_path = requested_path.lstrip("/").lstrip("\\")
    full_path = (project_dir / clean_req_path).resolve()
    
    # Check if the resolved path starts with the project directory
    if not str(full_path).startswith(str(project_dir.resolve())):
        raise HTTPException(status_code=403, detail="Acesso a arquivos fora do diretório do projeto proibido")
    
    return full_path

def build_file_tree(base_path: Path, relative_root: str = "") -> List[FileNode]:
    tree = []
    try:
        # Sort directories first, then files
        items = sorted(os.listdir(base_path), key=lambda x: (not os.path.isdir(base_path / x), x.lower()))
        
        for item in items:
            full_path = base_path / item
            rel_path = f"{relative_root}/{item}" if relative_root else item
            
            # Skip hidden files/dirs (optional, but good for cleanliness)
            if item.startswith(".") and item != ".env":
                continue
                
            if os.path.isdir(full_path):
                node = FileNode(
                    name=item,
                    path=rel_path,
                    type="directory",
                    children=build_file_tree(full_path, rel_path)
                )
                tree.append(node)
            else:
                node = FileNode(
                    name=item,
                    path=rel_path,
                    type="file",
                    size=os.path.getsize(full_path)
                )
                tree.append(node)
    except FileNotFoundError:
        return []
    return tree

@router.get("", response_model=List[FileNode])
async def list_files(
    project_id: int,
    current_user: User = Depends(get_current_user)
):
    """Lista estrutura de arquivos do projeto"""
    project_dir = get_project_dir(project_id)
    
    if not project_dir.exists():
        # Se não existir, retorna lista vazia ou cria?
        # Por enquanto lista vazia, o worker que cria a pasta
        return []
        
    return build_file_tree(project_dir)

@router.get("/content", response_model=FileContentResponse)
async def get_file_content(
    project_id: int,
    path: str = Query(..., description="Caminho relativo do arquivo"),
    current_user: User = Depends(get_current_user)
):
    """Lê conteúdo de um arquivo"""
    project_dir = get_project_dir(project_id)
    full_path = validate_path(project_dir, path)
    
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        
    try:
        # Tentar ler como utf-8
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        return FileContentResponse(path=path, content=content)
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Arquivo binário ou codificação não suportada")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler arquivo: {str(e)}")

@router.post("/content")
async def save_file_content(
    project_id: int,
    data: FileSaveRequest,
    current_user: User = Depends(get_current_user)
):
    """Salva conteúdo em um arquivo"""
    project_dir = get_project_dir(project_id)
    full_path = validate_path(project_dir, data.path)
    
    # Garantir que diretório pai existe
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(data.content)
        return {"message": "Arquivo salvo com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo: {str(e)}")
