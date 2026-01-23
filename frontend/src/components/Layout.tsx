'use client'

import WorkspaceLayout from './workspace/WorkspaceLayout'

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  return <WorkspaceLayout>{children}</WorkspaceLayout>
}
