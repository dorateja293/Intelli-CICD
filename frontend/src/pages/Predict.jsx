import FormInput from '../components/FormInput'
import Button from '../components/Button'
import { Sparkles, BrainCircuit } from 'lucide-react'

export default function Predict() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="page-title">AI Sandbox</h1>
        <p className="page-sub">Manually simulate the prediction engine with custom parameters</p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        <div className="lg:col-span-2 glass-panel p-8 border border-white/10">
          <div className="flex items-center gap-2 mb-6 text-white pb-4 border-b border-white/5">
            <BrainCircuit size={20} className="text-indigo-400"/>
            <h3 className="font-bold">Input Variables</h3>
          </div>
          <form className="space-y-5">
            <FormInput id="files" label="Files Changed" type="number" placeholder="e.g. 5" />
            <div className="grid grid-cols-2 gap-4">
              <FormInput id="added" label="Lines Added" type="number" placeholder="120" />
              <FormInput id="deleted" label="Lines Deleted" type="number" placeholder="45" />
            </div>
            <FormInput id="failRate" label="Hist. Failure Rate (%)" type="number" placeholder="12.5" />
            <div className="pt-4 mt-8 border-t border-white/5">
              <Button type="button" variant="indigo"><span className="flex items-center gap-2"><Sparkles size={16}/> Generate Prediction</span></Button>
            </div>
          </form>
        </div>
        
        <div className="lg:col-span-3 glass-panel p-8 bg-black/40 border border-white/5 flex flex-col items-center justify-center relative overflow-hidden group">
          <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-5"></div>
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-indigo-500/10 rounded-full blur-[80px] pointer-events-none group-hover:bg-indigo-500/20 transition-all duration-700"></div>
          
          <div className="text-center relative z-10">
            <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 mx-auto flex items-center justify-center mb-6">
              <Sparkles size={24} className="text-[#71717a]" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Awaiting Parameters</h3>
            <p className="text-[#a1a1aa] text-sm max-w-sm mx-auto">Fill out the variables on the left and hit generate to see how the AI weights the risk of failure.</p>
          </div>
        </div>
      </div>
    </div>
  )
}