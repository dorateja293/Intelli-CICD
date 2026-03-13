import ProjectCard from '../components/ProjectCard'
import Button from '../components/Button'
import { Plus } from 'lucide-react'

export default function Projects() {
  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="page-title">Repositories</h1>
          <p className="page-sub">Manage connected GitHub repositories and webhooks</p>
        </div>
        <div className="w-full sm:w-48">
          <Button variant="primary" size="sm"><span className="flex items-center gap-2"><Plus size={16}/> Add Repository</span></Button>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <ProjectCard name="core-service" repo="acme-corp/core-service" commits={'2.4k'} skipRate="42%" status="healthy" />
        <ProjectCard name="frontend-web" repo="acme-corp/frontend-web" commits={'1.2k'} skipRate="68%" status="healthy" />
        <ProjectCard name="payment-gateway" repo="acme-corp/payment-gateway" commits={'850'} skipRate="12%" status="failing" />
      </div>
    </div>
  )
}