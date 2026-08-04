import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { avatarColor } from '@/ui/avatar';

function MemberAvatar({ label, seed }: { label: string; seed: number }) {
  return (
    <Avatar size="lg" aria-label={label}>
      <AvatarFallback
        className="font-semibold text-white"
        style={{ backgroundColor: avatarColor(seed) }}
      >
        {label.slice(0, 1).toUpperCase()}
      </AvatarFallback>
    </Avatar>
  );
}

export { MemberAvatar };
