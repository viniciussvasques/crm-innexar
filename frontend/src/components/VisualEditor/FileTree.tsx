import React, { useState } from 'react';
import { FileNode } from '@/types/files';
import { ChevronRight, ChevronDown, FileCode, Folder, FolderOpen } from 'lucide-react';

interface FileTreeProps {
    data: FileNode[];
    onSelectFile: (path: string) => void;
    activeFile?: string;
    level?: number;
}

const FileTree: React.FC<FileTreeProps> = ({ data, onSelectFile, activeFile, level = 0 }) => {
    return (
        <div className="text-sm">
            {data.map((node) => (
                <FileTreeNode
                    key={node.path}
                    node={node}
                    onSelectFile={onSelectFile}
                    activeFile={activeFile}
                    level={level}
                />
            ))}
        </div>
    );
};

const FileTreeNode: React.FC<{ node: FileNode; onSelectFile: (path: string) => void; activeFile?: string; level: number }> =
    ({ node, onSelectFile, activeFile, level }) => {
        const [isOpen, setIsOpen] = useState(false);

        const isFolder = node.type === 'directory';
        const isActive = activeFile === node.path;

        const handleClick = () => {
            if (isFolder) {
                setIsOpen(!isOpen);
            } else {
                onSelectFile(node.path);
            }
        };

        return (
            <div>
                <div
                    className={`flex items-center gap-1 py-1 px-2 cursor-pointer hover:bg-white/5 transition-colors
                    ${isActive ? 'bg-blue-500/20 text-blue-300' : 'text-slate-400'}
                `}
                    style={{ paddingLeft: `${level * 12 + 8}px` }}
                    onClick={handleClick}
                >
                    {isFolder && (
                        <span className="text-slate-500">
                            {isOpen ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                        </span>
                    )}
                    {!isFolder && <span className="w-3" />} {/* Spacer */}

                    <span className={isFolder ? 'text-amber-400' : 'text-blue-400'}>
                        {isFolder ? (isOpen ? <FolderOpen className="w-4 h-4" /> : <Folder className="w-4 h-4" />) : <FileCode className="w-4 h-4" />}
                    </span>

                    <span className="truncate select-none">{node.name}</span>
                </div>

                {isFolder && isOpen && node.children && (
                    <FileTree
                        data={node.children}
                        onSelectFile={onSelectFile}
                        activeFile={activeFile}
                        level={level + 1}
                    />
                )}
            </div>
        );
    }

export default FileTree;
