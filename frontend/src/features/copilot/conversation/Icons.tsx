export function Icon({ name }: { name: 'chat' | 'desk' | 'plus' | 'send' | 'stop' | 'image' | 'trash' }) {
  const paths = {
    chat: <path d="M5 6.5A2.5 2.5 0 0 1 7.5 4h9A2.5 2.5 0 0 1 19 6.5v6a2.5 2.5 0 0 1-2.5 2.5H11l-4 3v-3.3A2.5 2.5 0 0 1 5 12.5z" />,
    desk: <><path d="M4 6h16v11H4z" /><path d="M8 20v-3m8 3v-3M8 10h8" /></>,
    plus: <path d="M12 5v14M5 12h14" />,
    send: <><path d="m5 12 14-7-4 14-3-6z" /><path d="m12 13 7-8" /></>,
    stop: <rect x="7" y="7" width="10" height="10" rx="1" />,
    image: <><rect x="4" y="5" width="16" height="14" rx="2" /><circle cx="9" cy="10" r="1.5" /><path d="m6 17 4-4 3 3 2-2 3 3" /></>,
    trash: <><path d="M6 7h12m-9 0V5h6v2m-8 0 1 12h8l1-12" /></>,
  }
  return <svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>
}
