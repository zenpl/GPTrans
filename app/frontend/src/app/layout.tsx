import './globals.css'
import type { Metadata } from 'next'
import { Toaster } from 'react-hot-toast'

export const metadata: Metadata = {
  title: 'GPTrans - OCR to Chinese Translation',
  description: 'Transform scanned documents to Chinese with intelligent typesetting',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body>
        <div className="min-h-screen bg-gray-50">
          <header className="bg-white border-b border-gray-200">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between h-16">
                <div className="flex items-center">
                  <h1 className="text-xl font-bold text-gray-900">GPTrans</h1>
                  <span className="ml-2 text-sm text-gray-500">OCR 智能翻译排版系统</span>
                </div>
                <div className="flex items-center space-x-4">
                  <nav className="hidden md:flex space-x-8">
                    <a href="/" className="text-gray-900 hover:text-primary-600">首页</a>
                    <a href="/books" className="text-gray-500 hover:text-primary-600">书籍管理</a>
                    <a href="/glossaries" className="text-gray-500 hover:text-primary-600">术语表</a>
                  </nav>
                </div>
              </div>
            </div>
          </header>
          
          <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
            {children}
          </main>
        </div>
        
        <Toaster position="top-right" />
      </body>
    </html>
  )
}