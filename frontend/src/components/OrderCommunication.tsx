'use client'

import React, { useState, useEffect, useRef } from 'react'
import { Send, Paperclip, Link as LinkIcon, FileText, Download, ExternalLink, AlertCircle, CheckCircle2 } from 'lucide-react'
import api from '@/lib/api'
import { toast } from '@/components/Toast'
import Button from '@/components/Button'
import Input from '@/components/Input'

interface Message {
  id: number
  sender_type: 'admin' | 'client'
  sender_name: string
  message: string | null
  message_type: string
  files: Array<{ name: string; url: string; size?: number; type?: string }> | null
  links: Array<{ title: string; url: string; description?: string }> | null
  is_important: boolean
  is_read: boolean
  created_at: string
}

interface OrderCommunicationProps {
  orderId: number
}

export default function OrderCommunication({ orderId }: OrderCommunicationProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [sending, setSending] = useState(false)
  const [messageText, setMessageText] = useState('')
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [links, setLinks] = useState<Array<{ title: string; url: string; description: string }>>([])
  const [showLinkForm, setShowLinkForm] = useState(false)
  const [linkForm, setLinkForm] = useState({ title: '', url: '', description: '' })
  const fileInputRef = useRef<HTMLInputElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const loadMessages = async () => {
    setLoadError(null)
    try {
      const response = await api.get(`/api/site-orders/${orderId}/messages`)
      setMessages(response.data?.messages ?? [])
    } catch (error: any) {
      console.error('Error loading messages:', error)
      const msg = error.response?.data?.error || error.response?.data?.detail || error.message || 'Erro ao carregar'
      setLoadError(typeof msg === 'string' ? msg : JSON.stringify(msg))
      setMessages([])
      toast.error('Erro ao carregar mensagens')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadMessages()
    // Auto-refresh every 10 seconds
    const interval = setInterval(loadMessages, 10000)
    return () => clearInterval(interval)
  }, [orderId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files))
    }
  }

  const handleUploadFiles = async () => {
    if (selectedFiles.length === 0) return

    setSending(true)
    try {
      const uploadedFiles: any[] = []
      
      for (const file of selectedFiles) {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('description', `Arquivo: ${file.name}`)

        const response = await api.post(`/api/site-orders/${orderId}/upload`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        
        uploadedFiles.push(...response.data.file)
      }

      // Enviar mensagem com arquivos
      await api.post(`/api/site-orders/${orderId}/messages`, {
        message: messageText || `Arquivo(s) enviado(s): ${selectedFiles.map(f => f.name).join(', ')}`,
        message_type: 'file',
        files: uploadedFiles
      })

      toast.success('Arquivo(s) enviado(s) com sucesso!')
      setMessageText('')
      setSelectedFiles([])
      if (fileInputRef.current) fileInputRef.current.value = ''
      loadMessages()
    } catch (error: any) {
      console.error('Error uploading files:', error)
      toast.error('Erro ao enviar arquivo(s)')
    } finally {
      setSending(false)
    }
  }

  const handleAddLink = () => {
    if (!linkForm.url) {
      toast.error('URL é obrigatória')
      return
    }
    setLinks([...links, { ...linkForm }])
    setLinkForm({ title: '', url: '', description: '' })
    setShowLinkForm(false)
  }

  const handleSendMessage = async () => {
    if (!messageText.trim() && selectedFiles.length === 0 && links.length === 0) {
      toast.error('Digite uma mensagem, anexe arquivos ou adicione links')
      return
    }

    setSending(true)
    try {
      // Se tem arquivos, fazer upload primeiro
      if (selectedFiles.length > 0) {
        await handleUploadFiles()
        return
      }

      // Enviar mensagem
      await api.post(`/api/site-orders/${orderId}/messages`, {
        message: messageText,
        message_type: links.length > 0 ? 'link' : 'message',
        links: links.length > 0 ? links : null
      })

      toast.success('Mensagem enviada!')
      setMessageText('')
      setLinks([])
      loadMessages()
    } catch (error: any) {
      console.error('Error sending message:', error)
      toast.error('Erro ao enviar mensagem')
    } finally {
      setSending(false)
    }
  }

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return ''
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const getFileUrl = (fileUrl: string) => {
    // Se é URL relativa, construir URL completa
    if (fileUrl.startsWith('/api/')) {
      return `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${fileUrl}`
    }
    return fileUrl
  }

  if (loading && messages.length === 0 && !loadError) {
    return <div className="text-center py-8 text-slate-400">Carregando mensagens...</div>
  }

  return (
    <div className="flex flex-col h-full min-h-[400px]">
      {loadError && (
        <div className="mb-4 p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center justify-between">
          <span className="text-red-300 text-sm">{loadError}</span>
          <Button variant="secondary" size="sm" onClick={() => { setLoading(true); loadMessages(); }}>Tentar novamente</Button>
        </div>
      )}
      {/* Messages List */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4 min-h-[300px] max-h-[500px]">
        {messages.length === 0 && !loadError ? (
          <div className="text-center py-8 text-slate-400">
            <FileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>Nenhuma mensagem ainda</p>
            <p className="text-sm mt-1">Envie uma mensagem, arquivo ou link para começar</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`p-4 rounded-lg border ${
                msg.sender_type === 'admin'
                  ? 'bg-blue-500/10 border-blue-500/30 ml-8'
                  : 'bg-slate-800/50 border-white/10 mr-8'
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-white">{msg.sender_name}</span>
                  {msg.is_important && (
                    <AlertCircle className="w-4 h-4 text-yellow-400" title="Importante" />
                  )}
                  {msg.sender_type === 'admin' && (
                    <span className="text-xs px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded">Equipe</span>
                  )}
                </div>
                <span className="text-xs text-slate-400">
                  {new Date(msg.created_at).toLocaleString('pt-BR')}
                </span>
              </div>

              {msg.message && (
                <p className="text-slate-300 mb-3 whitespace-pre-wrap">{msg.message}</p>
              )}

              {/* Files */}
              {msg.files && msg.files.length > 0 && (
                <div className="space-y-2 mb-3">
                  {msg.files.map((file, idx) => (
                    <a
                      key={idx}
                      href={getFileUrl(file.url)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 p-2 bg-white/5 rounded hover:bg-white/10 transition-colors"
                    >
                      <Paperclip className="w-4 h-4 text-slate-400" />
                      <span className="text-sm text-blue-400 flex-1">{file.name}</span>
                      {file.size && (
                        <span className="text-xs text-slate-500">{formatFileSize(file.size)}</span>
                      )}
                      <Download className="w-4 h-4 text-slate-400" />
                    </a>
                  ))}
                </div>
              )}

              {/* Links */}
              {msg.links && msg.links.length > 0 && (
                <div className="space-y-2">
                  {msg.links.map((link, idx) => (
                    <a
                      key={idx}
                      href={link.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-start gap-2 p-3 bg-white/5 rounded hover:bg-white/10 transition-colors"
                    >
                      <LinkIcon className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <div className="font-medium text-blue-400">{link.title || link.url}</div>
                        {link.description && (
                          <div className="text-sm text-slate-400 mt-1">{link.description}</div>
                        )}
                      </div>
                      <ExternalLink className="w-4 h-4 text-slate-400 flex-shrink-0" />
                    </a>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-white/10 pt-4 space-y-3">
        {/* Selected Files */}
        {selectedFiles.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {selectedFiles.map((file, idx) => (
              <div key={idx} className="flex items-center gap-2 px-2 py-1 bg-blue-500/20 rounded text-sm">
                <Paperclip className="w-3 h-3" />
                <span className="text-blue-400">{file.name}</span>
                <button
                  onClick={() => setSelectedFiles(selectedFiles.filter((_, i) => i !== idx))}
                  className="text-slate-400 hover:text-white"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Links to Add */}
        {links.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {links.map((link, idx) => (
              <div key={idx} className="flex items-center gap-2 px-2 py-1 bg-purple-500/20 rounded text-sm">
                <LinkIcon className="w-3 h-3" />
                <span className="text-purple-400">{link.title || link.url}</span>
                <button
                  onClick={() => setLinks(links.filter((_, i) => i !== idx))}
                  className="text-slate-400 hover:text-white"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Link Form */}
        {showLinkForm && (
          <div className="p-3 bg-white/5 rounded-lg space-y-2">
            <Input
              placeholder="Título do link (opcional)"
              value={linkForm.title}
              onChange={(e) => setLinkForm({ ...linkForm, title: e.target.value })}
            />
            <Input
              placeholder="URL *"
              value={linkForm.url}
              onChange={(e) => setLinkForm({ ...linkForm, url: e.target.value })}
              required
            />
            <Input
              placeholder="Descrição (opcional)"
              value={linkForm.description}
              onChange={(e) => setLinkForm({ ...linkForm, description: e.target.value })}
            />
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowLinkForm(false)
                  setLinkForm({ title: '', url: '', description: '' })
                }}
                className="text-xs"
              >
                Cancelar
              </Button>
              <Button type="button" onClick={handleAddLink} className="text-xs">
                Adicionar
              </Button>
            </div>
          </div>
        )}

        {/* Message Input */}
        <div className="flex gap-2">
          <textarea
            value={messageText}
            onChange={(e) => setMessageText(e.target.value)}
            placeholder="Digite sua mensagem..."
            className="flex-1 px-4 py-2 bg-slate-800 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/50 resize-none"
            rows={3}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && e.ctrlKey) {
                handleSendMessage()
              }
            }}
          />
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between">
          <div className="flex gap-2">
            <input
              ref={fileInputRef}
              type="file"
              multiple
              onChange={handleFileSelect}
              className="hidden"
              id="file-input"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="p-2 text-slate-400 hover:text-white hover:bg-white/10 rounded transition-colors"
              title="Anexar arquivo"
            >
              <Paperclip className="w-5 h-5" />
            </button>
            <button
              onClick={() => setShowLinkForm(!showLinkForm)}
              className="p-2 text-slate-400 hover:text-white hover:bg-white/10 rounded transition-colors"
              title="Adicionar link"
            >
              <LinkIcon className="w-5 h-5" />
            </button>
          </div>
          <Button
            onClick={handleSendMessage}
            disabled={sending || (!messageText.trim() && selectedFiles.length === 0 && links.length === 0)}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {sending ? (
              'Enviando...'
            ) : (
              <>
                <Send className="w-4 h-4 mr-2" />
                Enviar
              </>
            )}
          </Button>
        </div>
        <p className="text-xs text-slate-500">Ctrl+Enter para enviar</p>
      </div>
    </div>
  )
}
