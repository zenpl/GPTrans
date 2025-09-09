'use client'

import { use } from 'react'
import BookEditor from '@/components/BookEditor'

interface BookPageProps {
  params: Promise<{ id: string }>
}

export default function BookPage({ params }: BookPageProps) {
  const { id } = use(params)
  const bookId = parseInt(id, 10)

  if (isNaN(bookId)) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600">无效的书籍 ID</p>
      </div>
    )
  }

  return <BookEditor bookId={bookId} />
}