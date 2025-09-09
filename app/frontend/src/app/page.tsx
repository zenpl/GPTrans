'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, Languages, Download } from 'lucide-react'
import toast from 'react-hot-toast'
import { apiService } from '@/lib/api'
import { formatFileSize } from '@/lib/utils'

export default function HomePage() {
  const router = useRouter()
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)

  const onDrop = async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    // Validate file type
    const validTypes = ['image/jpeg', 'image/png', 'image/tiff', 'application/pdf']
    if (!validTypes.includes(file.type)) {
      toast.error('仅支持 JPG、PNG、TIFF 或 PDF 文件')
      return
    }

    // Validate file size (100MB max)
    if (file.size > 100 * 1024 * 1024) {
      toast.error('文件大小不能超过 100MB')
      return
    }

    setIsUploading(true)
    setUploadProgress(0)

    try {
      // Extract filename for book title
      const title = file.name.replace(/\.[^/.]+$/, '')
      
      // Upload file
      const book = await apiService.uploadBook(file, title)
      
      toast.success('文件上传成功！正在跳转到编辑页面...')
      
      // Redirect to book editor
      router.push(`/books/${book.id}`)
      
    } catch (error) {
      console.error('Upload failed:', error)
      toast.error('上传失败，请重试')
    } finally {
      setIsUploading(false)
      setUploadProgress(0)
    }
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'image/tiff': ['.tiff', '.tif'],
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    disabled: isUploading,
  })

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          智能文档翻译系统
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          将德语、瑞典语文档智能识别并翻译为中文，支持专业排版和多种格式导出
        </p>
      </div>

      {/* Upload Area */}
      <div className="max-w-2xl mx-auto">
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors
            ${isDragActive 
              ? 'border-primary-500 bg-primary-50' 
              : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
            }
            ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          <input {...getInputProps()} />
          
          <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          
          {isUploading ? (
            <div className="space-y-3">
              <p className="text-lg text-gray-600">正在上传文件...</p>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          ) : isDragActive ? (
            <p className="text-lg text-primary-600">释放鼠标开始上传</p>
          ) : (
            <div className="space-y-2">
              <p className="text-lg text-gray-600">
                拖拽文件到此处，或点击选择文件
              </p>
              <p className="text-sm text-gray-500">
                支持 JPG、PNG、TIFF、PDF 格式，最大 100MB
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Features */}
      <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
        <div className="text-center p-6 card">
          <FileText className="mx-auto h-12 w-12 text-primary-600 mb-4" />
          <h3 className="text-lg font-semibold mb-2">智能 OCR 识别</h3>
          <p className="text-gray-600">
            自动识别文档版面结构，准确提取文字内容和排版信息
          </p>
        </div>

        <div className="text-center p-6 card">
          <Languages className="mx-auto h-12 w-12 text-primary-600 mb-4" />
          <h3 className="text-lg font-semibold mb-2">专业翻译</h3>
          <p className="text-gray-600">
            支持德语、瑞典语到中文翻译，可配置术语表确保专业准确性
          </p>
        </div>

        <div className="text-center p-6 card">
          <Download className="mx-auto h-12 w-12 text-primary-600 mb-4" />
          <h3 className="text-lg font-semibold mb-2">智能排版</h3>
          <p className="text-gray-600">
            中文排版优化，自动断行禁则处理，导出 PDF 和 ePub 格式
          </p>
        </div>
      </div>

      {/* Recent Books */}
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">最近的项目</h2>
          <a 
            href="/books" 
            className="text-primary-600 hover:text-primary-700 font-medium"
          >
            查看全部 →
          </a>
        </div>
        
        <div className="card p-6 text-center text-gray-500">
          <p>暂无最近项目，请上传文档开始使用</p>
        </div>
      </div>
    </div>
  )
}