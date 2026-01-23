'use client'

import React, { useEffect, useState, useCallback, useRef } from 'react'
import { FileNode } from '@/types/files'
import FileTree from './FileTree'
import CodeEditor from './CodeEditor'
import api from '@/lib/api'
import { toast } from '@/components/Toast'
import { Save, RefreshCw, PanelLeft, Eye, FileCode, Globe } from 'lucide-react'
import Button from '@/components/Button'

interface VisualEditorProps {
    projectId: number
}

// Helper to determine language from extension
const getLanguage = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase()
    switch (ext) {
        case 'js': case 'jsx': return 'javascript'
        case 'ts': case 'tsx': return 'typescript'
        case 'html': return 'html'
        case 'css': return 'css'
        case 'json': return 'json'
        case 'py': return 'python'
        case 'md': return 'markdown'
        default: return 'plaintext'
    }
}

export default function VisualEditor({ projectId }: VisualEditorProps) {
    const [fileTree, setFileTree] = useState<FileNode[]>([])
    const [activeFile, setActiveFile] = useState<string | null>(null)
    const [fileContent, setFileContent] = useState<string>('')
    const [originalContent, setOriginalContent] = useState<string>('')
    const [loadingFiles, setLoadingFiles] = useState(false)
    const [loadingContent, setLoadingContent] = useState(false)
    const [saving, setSaving] = useState(false)
    const [showPreview, setShowPreview] = useState(true)

    const isDirty = fileContent !== originalContent

    // Load structure
    const loadFileTree = useCallback(async () => {
        setLoadingFiles(true)
        try {
            const res = await api.get<FileNode[]>(`/api/projects/${projectId}/files`)
            setFileTree(res.data)
        } catch (error) {
            console.error(error)
            toast.error('Failed to load file structure')
        } finally {
            setLoadingFiles(false)
        }
    }, [projectId])

    useEffect(() => {
        loadFileTree()
    }, [loadFileTree])

    // Load file content
    const handleSelectFile = async (path: string) => {
        if (isDirty) {
            if (!confirm('You have unsaved changes. Discard them?')) return
        }

        setActiveFile(path)
        setLoadingContent(true)
        try {
            const res = await api.get(`/api/projects/${projectId}/files/content`, { params: { path } })
            setFileContent(res.data.content)
            setOriginalContent(res.data.content)
        } catch (error) {
            console.error(error)
            toast.error('Failed to load file content')
            setFileContent('')
            setOriginalContent('')
        } finally {
            setLoadingContent(false)
        }
    }

    const handleSave = async () => {
        if (!activeFile) return
        setSaving(true)
        try {
            await api.post(`/api/projects/${projectId}/files/content`, { path: activeFile, content: fileContent })
            setOriginalContent(fileContent)
            toast.success('File saved')

            // Trigger preview refresh if needed (e.g. reload iframe)
            const iframe = document.getElementById('preview-frame') as HTMLIFrameElement
            if (iframe) iframe.contentWindow?.location.reload()

        } catch (error) {
            console.error(error)
            toast.error('Failed to save file')
        } finally {
            setSaving(false)
        }
    }

    return (
        <div className="flex h-[calc(100vh-64px)] bg-slate-950 overflow-hidden text-white border-t border-white/10">
            {/* Sidebar: File Tree */}
            <div className="w-64 border-r border-white/10 flex flex-col bg-slate-900/50">
                <div className="p-3 border-b border-white/10 flex justify-between items-center">
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Explorer</span>
                    <button onClick={loadFileTree} className="text-slate-500 hover:text-white transition-colors">
                        <RefreshCw className="w-3 h-3" />
                    </button>
                </div>
                <div className="flex-1 overflow-y-auto p-2">
                    {loadingFiles ? (
                        <div className="text-center p-4 text-xs text-slate-500">Loading...</div>
                    ) : (
                        <FileTree data={fileTree} onSelectFile={handleSelectFile} activeFile={activeFile || ''} />
                    )}
                </div>
            </div>

            {/* Main Editor Area */}
            <div className="flex-1 flex flex-col">
                {/* Editor Toolbar */}
                <div className="h-10 border-b border-white/10 bg-slate-900 flex items-center justify-between px-4">
                    <div className="flex items-center gap-2 text-sm text-slate-300">
                        {activeFile ? (
                            <>
                                <FileCode className="w-4 h-4 text-blue-400" />
                                <span>{activeFile}</span>
                                {isDirty && <span className="w-2 h-2 rounded-full bg-amber-400" title="Unsaved changes" />}
                            </>
                        ) : (
                            <span className="text-slate-500 italic">No file selected</span>
                        )}
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setShowPreview(!showPreview)}
                            className={`p-1.5 rounded hover:bg-white/10 transition-colors ${showPreview ? 'text-blue-400' : 'text-slate-400'}`}
                            title="Toggle Preview"
                        >
                            <Eye className="w-4 h-4" />
                        </button>
                        <Button
                            size="sm"
                            disabled={!isDirty || !activeFile}
                            onClick={handleSave}
                            isLoading={saving}
                            className="bg-blue-600 hover:bg-blue-500 text-xs px-3 h-7 flex items-center gap-1"
                        >
                            <Save className="w-3 h-3" /> Save
                        </Button>
                    </div>
                </div>

                {/* Editor Content */}
                <div className="flex-1 flex overflow-hidden relative">
                    <div className={`flex-1 flex flex-col transition-all duration-300 ${showPreview ? 'w-1/2' : 'w-full'}`}>
                        {activeFile ? (
                            loadingContent ? (
                                <div className="flex items-center justify-center h-full text-slate-500">Loading content...</div>
                            ) : (
                                <CodeEditor
                                    code={fileContent}
                                    language={getLanguage(activeFile)}
                                    onChange={(val) => setFileContent(val || '')}
                                />
                            )
                        ) : (
                            <div className="flex flex-col items-center justify-center h-full text-slate-500 bg-slate-900/30">
                                <PanelLeft className="w-12 h-12 mb-4 opacity-50" />
                                <p>Select a file to start editing</p>
                            </div>
                        )}
                    </div>

                    {/* Preview Pane */}
                    {showPreview && (
                        <div className="w-1/2 border-l border-white/10 bg-white flex flex-col">
                            <div className="h-8 bg-slate-100 border-b border-slate-200 flex items-center px-3 gap-2">
                                <Globe className="w-3 h-3 text-slate-400" />
                                <span className="text-xs text-slate-500 flex-1 truncate">http://localhost:3000/sites/{projectId}</span>
                            </div>
                            <div className="flex-1 bg-white relative">
                                <iframe
                                    id="preview-frame"
                                    src={`/api/projects/${projectId}/preview`} // TODO: Implement preview route
                                    className="w-full h-full border-0"
                                    title="Site Preview"
                                />
                                {/* Placeholder for MVP until preview route is ready */}
                                <div className="absolute inset-0 flex items-center justify-center bg-slate-50 pointer-events-none opacity-0">
                                    <p className="text-slate-400 text-sm">Preview Loading...</p>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
