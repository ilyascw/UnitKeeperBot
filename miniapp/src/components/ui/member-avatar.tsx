import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { avatarColor } from '@/ui/avatar';

function MemberAvatar({
  label,
  seed,
  photoUrl,
}: {
  label: string;
  seed: number;
  photoUrl?: string | null;
}) {
  return (
    <Avatar size="lg" aria-label={label}>
      {photoUrl ? <AvatarImage src={photoUrl} alt="" /> : null}
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
