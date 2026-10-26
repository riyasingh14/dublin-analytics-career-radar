import { ArrowUpRight, Github, Linkedin, Mail } from "lucide-react";

export default function BuilderContacts() {
  return <div className="builder-actions">
    <a href="https://www.linkedin.com/in/riya-singh-business-analyst/" target="_blank" rel="noreferrer" aria-label="Connect on LinkedIn"><Linkedin size={15} /> LinkedIn <ArrowUpRight size={13} /></a>
    <a href="https://github.com/riyasingh14" target="_blank" rel="noreferrer" aria-label="Riya’s GitHub profile"><Github size={15} /> GitHub <ArrowUpRight size={13} /></a>
    <a href="mailto:kashyapriya2020@gmail.com" aria-label="Email Riya at kashyapriya2020@gmail.com"><Mail size={15} /> Email <ArrowUpRight size={13} /></a>
  </div>;
}
