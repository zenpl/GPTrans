'use client'

import { useState, useEffect, useCallback } from 'react'
import { Block, Page, Book } from '@/types'
import { apiService } from '@/lib/api'
import { getBlockTypeLabel, getStatusLabel, getStatusColor, cn } from '@/lib/utils'
import { 
  Eye, Edit3, Download, Settings, RefreshCw, 
  ChevronLeft, ChevronRight, Compress, Save 
} from 'lucide-react'
import toast from 'react-hot-toast'

interface BookEditorProps {
  bookId: number
}

export default function BookEditor({ bookId }: BookEditorProps) {
  const [book, setBook] = useState<Book | null>(null)
  const [pages, setPages] = useState<Page[]>([])
  const [blocks, setBlocks] = useState<Block[]>([])
  const [selectedBlockId, setSelectedBlockId] = useState<number | null>(null)
  const [editingBlockId, setEditingBlockId] = useState<number | null>(null)
  const [editingText, setEditingText] = useState('')
  const [currentPageIndex, setCurrentPageIndex] = useState(0)
  const [viewMode, setViewMode] = useState<'original' | 'preview'>('original')
  const [isLoading, setIsLoading] = useState(true)
  const [isProcessing, setIsProcessing] = useState(false)

  const loadData = useCallback(async () => {
    try {
      setIsLoading(true)
      const [bookData, blocksData] = await Promise.all([
        apiService.getBook(bookId),
        apiService.getBookBlocks(bookId),
      ])
      
      setBook(bookData)
      setBlocks(blocksData)
      
      // Extract unique pages from blocks
      const pageIds = [...new Set(blocksData.map(block => block.page_id))]
      // In a real app, we'd fetch actual page data with dimensions and image URLs
      const pagesData = pageIds.map((pageId, index) => ({
        id: pageId,
        book_id: bookId,
        index,
        image_url: `/static/books/${bookId}/page_${index}.png`,
        width: 1240,
        height: 1754,
        dpi: 150
      }))
      setPages(pagesData)
      
    } catch (error) {
      console.error('Failed to load book data:', error)
      toast.error('加载失败')
    } finally {
      setIsLoading(false)
    }
  }, [bookId])

  useEffect(() => {
    loadData()
  }, [loadData])

  const currentPage = pages[currentPageIndex]
  const currentPageBlocks = blocks.filter(block => 
    currentPage ? block.page_id === currentPage.id : false
  ).sort((a, b) => a.order - b.order)

  const handleBlockClick = (block: Block) => {
    setSelectedBlockId(block.id)
    setEditingBlockId(null)
  }

  const handleBlockEdit = (block: Block) => {
    setEditingBlockId(block.id)
    setEditingText(block.text_translated || block.text_source)
    setSelectedBlockId(block.id)
  }

  const handleSaveEdit = async () => {
    if (!editingBlockId || !editingText.trim()) return
    
    try {
      await apiService.updateBlock(editingBlockId, {
        text_translated: editingText,
        status: 'translated'
      })
      
      // Update local state
      setBlocks(prev => prev.map(block => 
        block.id === editingBlockId 
          ? { ...block, text_translated: editingText, status: 'translated' }
          : block
      ))
      
      setEditingBlockId(null)
      toast.success('保存成功')
    } catch (error) {
      console.error('Failed to update block:', error)
      toast.error('保存失败')
    }
  }

  const handleCancelEdit = () => {
    setEditingBlockId(null)
    setEditingText('')
  }

  const handleNormalizeOCR = async () => {
    try {
      setIsProcessing(true)
      const result = await apiService.normalizeOCR(bookId)
      toast.success('OCR 处理已开始，请等待完成')
      // In a real app, we'd poll for job status
      setTimeout(loadData, 3000)
    } catch (error) {
      console.error('OCR normalization failed:', error)
      toast.error('OCR 处理失败')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleTranslate = async () => {
    try {
      setIsProcessing(true)
      const result = await apiService.translateBook(bookId, {
        length_hint: 'normal'
      })
      toast.success('翻译已开始，请等待完成')
      setTimeout(loadData, 5000)
    } catch (error) {
      console.error('Translation failed:', error)
      toast.error('翻译失败')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleExport = async (formats: string[]) => {
    try {
      setIsProcessing(true)
      const result = await apiService.exportBook(bookId, { formats })
      toast.success('导出已开始，请等待完成')
    } catch (error) {
      console.error('Export failed:', error)
      toast.error('导出失败')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleCompressTranslation = async (blockId: number) => {
    const block = blocks.find(b => b.id === blockId)
    if (!block?.text_translated) return

    try {
      // This would call a concise translation API
      toast.success('压缩翻译功能开发中...')
    } catch (error) {
      toast.error('压缩失败')
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="animate-spin h-8 w-8 text-primary-600" />
        <span className="ml-2">加载中...</span>
      </div>
    )
  }

  if (!book) {
    return <div>未找到书籍</div>
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">{book.title}</h1>
            <p className="text-sm text-gray-600">
              {book.source_lang.toUpperCase()} → {book.target_lang}
            </p>
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={handleNormalizeOCR}
              disabled={isProcessing}
              className="btn-secondary flex items-center space-x-2"
            >
              <RefreshCw className={cn("h-4 w-4", isProcessing && "animate-spin")} />
              <span>OCR 识别</span>
            </button>
            
            <button
              onClick={handleTranslate}
              disabled={isProcessing}
              className="btn-secondary flex items-center space-x-2"
            >
              <Edit3 className="h-4 w-4" />
              <span>翻译</span>
            </button>
            
            <div className="relative group">
              <button className="btn-primary flex items-center space-x-2">
                <Download className="h-4 w-4" />
                <span>导出</span>
              </button>
              
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all">
                <div className="py-1">
                  <button
                    onClick={() => handleExport(['pdf'])}
                    className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
                  >
                    导出为 PDF
                  </button>
                  <button
                    onClick={() => handleExport(['epub'])}
                    className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
                  >
                    导出为 ePub
                  </button>
                  <button
                    onClick={() => handleExport(['pdf', 'epub'])}
                    className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
                  >
                    导出全部格式
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 flex">
        {/* Main Editor */}
        <div className="flex-1 flex">
          {/* Page Navigation */}
          {pages.length > 1 && (
            <div className="w-16 bg-gray-100 border-r border-gray-200 flex flex-col items-center py-4 space-y-2">
              <button
                onClick={() => setCurrentPageIndex(Math.max(0, currentPageIndex - 1))}
                disabled={currentPageIndex === 0}
                className="p-2 rounded-md hover:bg-gray-200 disabled:opacity-50"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              
              <span className="text-sm font-medium">
                {currentPageIndex + 1}/{pages.length}
              </span>
              
              <button
                onClick={() => setCurrentPageIndex(Math.min(pages.length - 1, currentPageIndex + 1))}
                disabled={currentPageIndex === pages.length - 1}
                className="p-2 rounded-md hover:bg-gray-200 disabled:opacity-50"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          )}

          {/* Page Content */}
          <div className="flex-1 relative bg-gray-900 overflow-auto">
            {currentPage && (
              <div className="relative mx-auto" style={{ width: currentPage.width, height: currentPage.height }}>
                {/* Page Image (placeholder) */}
                <div 
                  className="absolute inset-0 bg-white border"
                  style={{ width: currentPage.width, height: currentPage.height }}
                >
                  <div className="flex items-center justify-center h-full text-gray-400">
                    页面图片加载中...
                  </div>
                </div>

                {/* Block Overlays */}
                {currentPageBlocks.map((block) => (
                  <div
                    key={block.id}
                    className={cn(
                      "block-frame",
                      selectedBlockId === block.id && "selected"
                    )}
                    style={{
                      left: block.bbox_x,
                      top: block.bbox_y,
                      width: block.bbox_w,
                      height: block.bbox_h,
                    }}
                    onClick={() => handleBlockClick(block)}
                  >
                    <div className="absolute -top-6 left-0 text-xs bg-blue-600 text-white px-1 rounded">
                      {getBlockTypeLabel(block.type)}
                    </div>
                    
                    {viewMode === 'preview' && block.text_translated && (
                      <div className="p-2 chinese-text text-sm overflow-hidden">
                        {block.text_translated}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Side Panel */}
        <div className="w-96 bg-white border-l border-gray-200 flex flex-col">
          {/* View Mode Toggle */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex rounded-lg bg-gray-100 p-1">
              <button
                onClick={() => setViewMode('original')}
                className={cn(
                  "flex-1 py-2 px-3 text-sm font-medium rounded-md transition-colors",
                  viewMode === 'original' 
                    ? "bg-white text-gray-900 shadow-sm" 
                    : "text-gray-500 hover:text-gray-700"
                )}
              >
                原图模式
              </button>
              <button
                onClick={() => setViewMode('preview')}
                className={cn(
                  "flex-1 py-2 px-3 text-sm font-medium rounded-md transition-colors",
                  viewMode === 'preview' 
                    ? "bg-white text-gray-900 shadow-sm" 
                    : "text-gray-500 hover:text-gray-700"
                )}
              >
                预览模式
              </button>
            </div>
          </div>

          {/* Block List */}
          <div className="flex-1 overflow-auto">
            <div className="p-4">
              <h3 className="font-medium text-gray-900 mb-3">文本块</h3>
              <div className="space-y-3">
                {currentPageBlocks.map((block) => (
                  <div
                    key={block.id}
                    className={cn(
                      "p-3 border rounded-lg cursor-pointer transition-colors",
                      selectedBlockId === block.id 
                        ? "border-red-300 bg-red-50" 
                        : "border-gray-200 hover:border-gray-300"
                    )}
                    onClick={() => handleBlockClick(block)}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-xs font-medium text-gray-600">
                        {getBlockTypeLabel(block.type)}
                      </span>
                      <span className={cn("badge", getStatusColor(block.status))}>
                        {getStatusLabel(block.status)}
                      </span>
                    </div>
                    
                    <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                      {block.text_source}
                    </p>
                    
                    {block.text_translated && (
                      <div className="pt-2 border-t border-gray-100">
                        <p className="text-sm chinese-text text-gray-900 line-clamp-3">
                          {block.text_translated}
                        </p>
                      </div>
                    )}
                    
                    <div className="flex justify-between items-center mt-2">
                      <div className="flex space-x-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleBlockEdit(block)
                          }}
                          className="text-blue-600 hover:text-blue-700 text-xs"
                        >
                          <Edit3 className="h-3 w-3 inline mr-1" />
                          编辑
                        </button>
                        
                        {block.text_translated && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleCompressTranslation(block.id)
                            }}
                            className="text-orange-600 hover:text-orange-700 text-xs"
                          >
                            <Compress className="h-3 w-3 inline mr-1" />
                            压缩
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Editor Panel */}
          {editingBlockId && (
            <div className="border-t border-gray-200 p-4">
              <div className="flex justify-between items-center mb-3">
                <h4 className="font-medium text-gray-900">编辑译文</h4>
                <div className="flex space-x-2">
                  <button
                    onClick={handleSaveEdit}
                    className="btn-primary text-sm flex items-center space-x-1"
                  >
                    <Save className="h-3 w-3" />
                    <span>保存</span>
                  </button>
                  <button
                    onClick={handleCancelEdit}
                    className="btn-secondary text-sm"
                  >
                    取消
                  </button>
                </div>
              </div>
              
              <textarea
                value={editingText}
                onChange={(e) => setEditingText(e.target.value)}
                className="w-full h-32 text-sm border border-gray-300 rounded-lg p-3 chinese-text focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                placeholder="输入译文..."
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}