#!/usr/bin/env ruby

class Spl
  attr_accessor :title

  def initialize (title=nil)
    @title = title || Wordlist.titles
  end

  def generate
    @queue = []
    @chars = CharacterList.new(queue)
    yield @chars
    return "#{title}.\n\n\n\n" +
      "#{@chars.to_s}\n\n" +
      "#{q_to_s}"
  end

private
  attr_accessor :queue
  def q_to_s ()
    scenes = q_to_scenes()
    ret = "\tAct I: The moment of truth.\n\n" +
      "\tScene I: #{Wordlist.descriptions}.\n\n"
    on_stage = []
    scenes.each do |chars, scene|
      # Insert Enter and exit
      if (exiting = on_stage - chars).length > 0
        ret += "[" + (exiting.length == 1 ? 'Exit ' : 'Exeunt ') +
          exiting.join(' and ') + # always 2 chars on stage => no need for ','
          "]\n"
      end
      ret += "[Enter " + (chars - on_stage).join(' and ') + "]\n"
      on_stage = chars
      # Insert dialogs
      last = nil
      scene.each do |char, dial|
        if last != char
          ret += "\n" + (on_stage - [char]).first + ":\n"
          last = char
        end
        ret += "\t#{dial}\n"
      end
      ret += "\n\n\n"
    end
    ret
  end

  def q_to_scenes ()
    current_char = []
    ret = []
    scene = []
    queue.each do |char, dia|
      unless current_char.include?(char)
        if current_char.length < 2
          current_char << char
        else
          ret << [current_char, scene]
          current_char = [char]
          scene = []
        end
      end
      scene << [char, dia]
    end
    # Complete the stage to have 2 characters
    if ret.length > 0
      current_char << ret.last[0].first if current_char.length < 2 # ie == 1
    else
      # This means less than 2 characters have been declared
      current_char << @chars.new('dummy_variable').name while \
        current_char.length < 2
    end
    ret << [current_char,scene]
  end
end

# A wrapper of all variables
class CharacterList
  def initialize (queue)
    @queue = queue
    @vars = {}
    @vars_map = {}
  end
  
  def length
    @vars.length
  end
  def to_s
    ret = ""
    @vars.each do |k,v|
      ret += "#{k}, #{Wordlist.descriptions}.\n"
    end
    ret
  end

  def method_missing (name)
    self.instance_eval <<-end_eval
      def #{name}
        self.send :get_var, "#{name}"
      end
    end_eval
    new name
  end

  def get_var (id)
    @vars[@vars_map[id.to_sym]]
  end
  def new (id)
    v = Variable.new(@queue) while v.nil? || @vars.has_key?(v.name)
    @vars[v.name] = v
    @vars_map[id] = v.name
    v
  end
end

# Wrapper for SPL variables
class Variable
  attr_accessor :name
  def initialize(queue)
    @name = Wordlist.character
    @queue = queue
  end
  
  def queue (s)
    @queue << [@name, s]
  end

  def push (val)
    if val.is_a?(String)
      val.bytes.reverse.each {|c| self.push c }
    elsif val.is_a?(Integer)
      queue "Remember #{val.to_spl.downcase}."
    else
      puts "Push ignored, arg. must be a String or an Integer, got #{val.to_s}"
    end
  end

  def pop
    queue "Recall those times of pure happiness."
  end

  def set (val)
    if val.is_a?(Integer)
      queue "#{Wordlist.second_person.capitalize} are as " +
        "#{Wordlist.neutral_adjective.downcase} as #{val.to_spl.downcase}!"
    else
      puts "Set ignored, arg. must be an Integer, got #{val.to_s}"
    end
  end

  def take (from, val)
    from.push "#{val[:flag_id]}\0#{val[:password]}\0#{val[:flag]}"
    queue "#{Wordlist.take.capitalize} " +
      "#{Wordlist.first_person_possessive.downcase} " +
      "#{Wordlist.banner.downcase}!"
  end

  def gimme (from, val)
    from.push "#{val[:flag_id]}\0#{val[:password]}"
    queue "#{Wordlist.gimme.capitalize} " +
      "#{Wordlist.second_person_possessive.downcase} " +
      "#{Wordlist.banner.downcase}!"
  end

  def to_c
    queue "Speak #{Wordlist.second_person_possessive.downcase} mind!"
  end
  def to_i
    queue "Open #{Wordlist.second_person_possessive.downcase} heart!"
  end
end

# A extention of Integer class to transform to SPL
class Integer
  def to_spl
    ret = []
    mask = 1
    pow_mask = 0
    while mask <= self
      if mask & self > 0
        s = Wordlist.positive_noun
        pow_mask.times {s = "#{Wordlist.positive_adjective} #{s}"}
        s = "the #{s}"
        ret << s
      end
      mask *= 2
      pow_mask += 1
    end
    ret << Wordlist.nothing if ret.length == 0
    t = ret.pop
    return ret.inject(t) { |r, n| "the sum of #{n} and #{r}"}
  end
end

class Wordlist
  def self.method_missing(name)
    if self.class_variable_defined?("@@#{name}")
      tab = self.class_variable_get("@@#{name}")
      return tab[Random.rand(tab.length)]
    else
      super
    end
  end

@@article = ["a", "an", "the", ]
@@banner = ["flag", "banner", "standard", "pennant", "streamer", "banneret", "booty", ]
@@be = ["am", "are", "art", "be", "is", ]
@@character = ["Achilles", "Adonis", "Adriana", "Aegeon", "Aemilia", "Agamemnon", "Agrippa", "Ajax", "Alonso", "Andromache", "Angelo", "Antiochus", "Antonio", "Arthur", "Autolycus", "Balthazar", "Banquo", "Beatrice", "Benedick", "Benvolio", "Bianca", "Brabantio", "Brutus", "Capulet", "Cassandra", "Cassius", "Christopher Sly", "Cicero", "Claudio", "Claudius", "Cleopatra", "Cordelia", "Cornelius", "Cressida", "Cymberline", "Demetrius", "Desdemona", "Dionyza", "Doctor Caius", "Dogberry", "Don John", "Don Pedro", "Donalbain", "Dorcas", "Duncan", "Egeus", "Emilia", "Escalus", "Falstaff", "Fenton", "Ferdinand", "Ford", "Fortinbras", "Francisca", "Friar John", "Friar Laurence", "Gertrude", "Goneril", "Hamlet", "Hecate", "Hector", "Helen", "Helena", "Hermia", "Hermonie", "Hippolyta", "Horatio", "Imogen", "Isabella", "John of Gaunt", "John of Lancaster", "Julia", "Juliet", "Julius Caesar", "King Henry", "King John", "King Lear", "King Richard", "Lady Capulet", "Lady Macbeth", "Lady Macduff", "Lady Montague", "Lennox", "Leonato", "Luciana", "Lucio", "Lychorida", "Lysander", "Macbeth", "Macduff", "Malcolm", "Mariana", "Mark Antony", "Mercutio", "Miranda", "Mistress Ford", "Mistress Overdone", "Mistress Page", "Montague", "Mopsa", "Oberon", "Octavia", "Octavius Caesar", "Olivia", "Ophelia", "Orlando", "Orsino", "Othello", "Page", "Pantino", "Paris", "Pericles", "Pinch", "Polonius", "Pompeius", "Portia", "Priam", "Prince Henry", "Prospero", "Proteus", "Publius", "Puck", "Queen Elinor", "Regan", "Robin", "Romeo", "Rosalind", "Sebastian", "Shallow", "Shylock", "Slender", "Solinus", "Stephano", "Thaisa", "The Abbot of Westminster", "The Apothecary", "The Archbishop of Canterbury", "The Duke of Milan", "The Duke of Venice", "The Ghost", "Theseus", "Thurio", "Timon", "Titania", "Titus", "Troilus", "Tybalt", "Ulysses", "Valentine", "Venus", "Vincentio", "Viola", "Spock", "Picard", "Kirk", "Darth Vader", "Han Solo", "Princess Leia", "Data", "Riker", "MacGyver", "Scotty", "Worf", "McCoy", ]
@@descriptions = ["moiety competent", "fellow", "nunnery", "body", "chopine", "fellow", "mineral of metals base", "sisterhood of holy nuns", "wise and virtuous", "man's life's no more than to say 'One", "most instant tetter bark'd about", "felon here", "prayer or two", "tackled stair", "king", "sight as this", "very drab", "drunkard reels", "masterly report", "poison", "short tale to make", "dead man in his shroud", "maid at your window", "fetch of wit", "brawl", "feast", "Capulet", "postscript here", "tear", "tortoise hung", "sweet goose", "crow", "needy time", "winning match", "pair of reechy kisses", "friend on Denmark", "man to double business bound", "neutral to his will and matter", "like goodness still", "foolish figure", "double varnish on the fame", "blister there", "common bound", "tithe", "man", "comma 'tween their amities", "quality", "kind of easiness", "curse in having her", "pleasant sleep", "suit", "spendthrift sigh", "wretched puling fool", "kind of joy", "custom", "man as Hamlet is", "hollow friend doth try", "minute than he will stand", "larger tether may he walk", "look so piteous in purport", "martial scorn", "silk thread plucks it back again", "sudden vigour doth posset", "wanton's bird", "wary eye", "knavish piece of work", "poperin pear", "letter", "sigh", "most select and generous chief in that", "man", "Montague", "man of wax", "lamp", "deed", "king's remembrance", "toil", "vault", "winged messenger of heaven", "king", "father", "tomb", "virtue", "little soil'd i' the working", "club", "grass", "stone", "little shaking of mine arm", "pirate of very warlike appointment gave us", "scratch", "seat", "soldier", "Tartar's painted bow of lath", "beast", "ghostly confessor", "thing immortal as itself", "foe", "dream", "fire sparkling in lovers' eyes", "sea nourish'd with lovers' tears", "man", "gipsy", "sponge", "spirit of health or goblin damn'd", "sick man in sadness make his will", "man to", "thousand times", "hare that is hoar", "straw", "maid", "fine", "lamb", "dream of passion", "farm and carters", "misbehaved and sullen wench", "foul disease", "gentleman", "joy past joy calls out on me", "noise did scare me from the tomb", "gentleman of the", "crafty madness", "rear", "father", "name", "ghost of him that lets me", "face", "month", "lightning", "Jack in thy mood as", "fearful point", "man to bow in the hams", "gentleman would see", "while", "handsome", "promised march", "dead man interr'd", "week", "new commission", "cave", "good turn for them", "seal'd compact", "tailor for wearing", "general groan", "good end", "gulf", "man", "prince's doom", "certain term to walk the night", "doubt", "liar", "' were lustier than he is", "team of little atomies", "sterile promontory", "pipe", "maiden blush bepaint my cheek", "tavern claps me his sword", "prologue to my brains", "bride", "quarrel", "fast", "cry of players", "jaunt have I had", "shrouding sheet", "kind of confession in your looks", "plurisy", "holy man", "grandsire phrase", "minute there are many days", "story of more woe", "guest is meet", "wish", "man might play", "great natural", "question left us yet to prove", "throne where honour may be crown'd", "house of tears", "pitiful case", "friend", "queen", "woman", "word with one of you", "place", "case to put my visage in", "torch", "daughter", "further edge", "desperate man", "plot", "foul thing", "letter to his father's house", "sudden day of joy", "brace of kinsmen", "defeated joy", "word", "portly gentleman", "wound", "grey", "frock or livery", "highway to my bed", "sigh so piteous and profound", "foot", "mildew'd ear", "caitiff wretch would sell it him", "skull now", "friend", "coil", "gentleman of Normandy", "small grey", "joyful bride", "great while", "stage be placed to the view", "man well", "ward two years ago", "falconer's voice", "weak supposal of our worth", "toy in blood", "great man's memory may outlive his life half", "note of", "day", "conduit", "happiness", "lash that speech doth give my conscience", "man", "satyr", "widow", "matron's bones", "man as you", "god", "course", "woman", "great buyer of land", "gorgeous palace", "friar with speed", "towering passion", "nobleman in town", "sore decayer of your whoreson dead body", "strumpet", "little way above our heads", "forged process of my death", "tender thing", "kinsman vex'd", "tedious tale", "Capulet", "murder done in Vienna", "score", "guest", "damned ghost that we have seen", "poison temper'd by himself", "prison", "will most incorrect to heaven", "more removed ground", "grief", "deal of brine", "better love to", "sexton's spade", "fellow", "delicate and tender prince", "maid", "state", "purposed evil", "true gentleman", "poor prisoner in his twisted gyves", "rich jewel in an Ethiope's ear", "paradox", "skitless soldier's flask", "murdering", "joyful woman", "little prating thing", "better proposer could", "smoke raised with the fume of sighs", "man", "wart", "morning hath he there been seen", "fool", "merry whoreson", "beauteous flower when next we meet", "piece of marchpane", "word", "foul and pestilent congregation of vapours", "grave man", "politician", "hole to keep the wind away", "bird's nest soon when it is dark", "whore", "stranger in the world", "hundred words", "king of infinite space", "part", "brain", "lender be", "day as this", "heaven", "villain", "lenten pie", "sleep to say we end", "whit", "messenger to bring it thee", "little", "mad", "round little worm", "medlar tree", "second leave", "despised life closed in my breast", "poor 'pothecary", "quarrel", "robustious", "cup of wine", "vice of kings", "passionate speech", "hair less", "sorrow", "new", "sickly part of one true sense", "winking", "hurdle thither", "creature native and indued", "tanner will last you nine year", "apology", "charnel", "sea of troubles", "little shuffling", "buried corse", "sad burial feast", "passion to tatters", "pair of stainless maidenhoods", "plentiful lack of", "dead man's tomb", "maid", "beggar", "man", "sparrow", "shadow's shadow", "'", "king", "villain", "French salutation", "dishclout to him", "letter", "fool", "child", "tale of bawdry", "crow", "dirty shovel", "while", "very toad", "grace was seated on this brow", "scourge is laid upon your hate", "higher rate", "joyful bride", "list of lawless resolutes", "ball", "trencher", "gun", "quarter", "back or second", "thing to you from his majesty", "wall to expel the winter flaw", "fair presence and put off these frowns", "mistress that is passing fair", "desperate tender", "knowing ear", "week", "painted tyrant", "king", "radiant angel link'd", "blow", "soldier's neck", "courtier's nose", "knife in it", "snowy dove trooping with crows", "handsaw", "gentleman to be her bridegroom", "peace", "man", "little", "hideous crash", "dead man leave", "speech of some dozen or sixteen lines", "dream", "man may strain courtesy", "house", "match", "fault to heaven", "sight as this", "command to parley", "month", "riotous head", "consummation", "fantasy and trick of fame", "shelf the precious diadem stole", "play", "stomach in't", "mother stain'd", "sight indeed", "visor and could tell", "loathed enemy", "truth", "dear father murder'd", "tyrannous and damned light", "grosser name", "wife", "villain", "hole", "vile phrase", "case as yours", "weak slave", "most pitiful ambition", "pipe for fortune's finger", "shot", "sepulchre", "roar", "maid", "dew", "thing", "righteous kiss", "fiery mind", "chough", "pair of indentures", "lightness", "weakness", "minute", "dozen friends", "play to", "divinity that shapes our ends", "king", "wife", "most emulate pride", "' gaming", "silk", "kind of", "beast", "Montague", "living monument", "feasting presence full of light", "Montague", "questionable shape", "wind", "golden axe", "shape of heaven", "pretty age", "hair more", "brother's hand", "kiss I die", "form of wax", "most", "' lies asleep", "bung", "mountain you have made", "bad", "pleasing shape", "preparation 'gainst the Polack", "poison", "cover", "virtuous and well", "torch", "ladder", "man", "weary life", "month", "restorative", "halfpenny", "tender thing", "wind", "grave", "spirit in his mistress' circle", "jest shall come about", "difference", "requiem and such rest to her", "tender kiss", "sin", "greeting", "broad goose", "wagoner", "bawd than the", "smock", "Montague", "Juliet", "bout with you", "seeming man", "bank of flowers", "fearful summons", "rapier's point", "wretch whose natural gifts were poor", "subject as myself", "more horrid hent", "gossip's bowl", "soul of", "brothel", "virtuous", "fishmonger", "beer", "little patch of ground", "trifling foolish banquet towards", "taste", "scarf", "friend or two", "solemn wager on your cunnings", "measure", "princox", "mask", "show", "holy man", "man", "note", "poison", "madness most discreet", "nunnery", "word", "word of joy", "cup", "rose", "massy wheel", "torch", "fiend", "surgeon", "robe", "sudden one hath wounded me", "time", "guest", "disgrace to them", "usurer", "puff'd and reckless libertine", "rat", "raven's back", "little from her hand", "lamentable thing", "foolish prating knave", "public count I might not go", "shame", "celestial bed", "man for cracking nuts", "bare bodkin", "dropping eye", "clout upon that head", "vial", "soul of lead", "sudden calm", "dried herring", "crocodile", "gib", "forest of feathers", "feeling loss", "lover", "saucy boy", "glass", "mutiny among my guests", "distemper'd head", "free visitation", "crab", "star i' the darkest night", ]
@@first_person_possessive = ["mine", "my", ]
@@first_person_reflexive = ["myself", ]
@@first_person = ["I", "me", ]
@@gimme = ["gimme", "give me", "show me", "expose", "surrender", "give up", "yield", ]
@@negative_adjective = ["bad", "cowardly", "cursed", "damned", "dirty", "disgusting", "distasteful", "dusty", "evil", "fat", "fat-kidneyed", "fatherless", "foul", "hairy", "half-witted", "scruffy-looking", "horrible", "horrid", "infected", "lying", "miserable", "misused", "oozing", "rotten", "rotten", "smelly", "snotty", "sorry", "stinking", "stuffed", "stupid", "vile", "villainous", "worried", ]
@@negative_comparative = ["punier", "smaller", "worse", ]
@@negative_noun = ["Hell", "Microsoft", "bastard", "beggar", "blister", "codpiece", "coward", "curse", "death", "devil", "draught", "famine", "flirt-gill", "goat", "hate", "hog", "hound", "leech", "lie", "pig", "plague", "starvation", "toad", "war", "wolf", "nerf-herder", ]
@@neutral_adjective = ["big", "black", "blue", "bluest", "bottomless", "furry", "green", "hard", "huge", "large", "little", "normal", "old", "purple", "red", "rural", "small", "tiny", "white", "yellow", ]
@@neutral_noun = ["animal", "aunt", "brother", "cat", "chihuahua", "cousin", "cow", "daughter", "door", "face", "father", "fellow", "granddaughter", "grandfather", "grandmother", "grandson", "hair", "hamster", "horse", "lamp", "lantern", "mistletoe", "moon", "morning", "mother", "nephew", "niece", "nose", "purse", "road", "roman", "sister", "sky", "son", "squirrel", "stone wall", "thing", "town", "tree", "uncle", "wind", ]
@@nothing = ["nothing", "zero", ]
@@positive_adjective = ["amazing", "beautiful", "blossoming", "bold", "brave", "charming", "clearest", "cunning", "cute", "delicious", "embroidered", "fair", "fine", "gentle", "golden", "good", "handsome", "happy", "healthy", "honest", "lovely", "loving", "mighty", "noble", "peaceful", "pretty", "prompt", "proud", "reddest", "rich", "smooth", "sunny", "sweet", "sweetest", "trustworthy", "warm", ]
@@positive_comparative = ["better", "bigger", "fresher", "friendlier", "nicer", "jollier", ]
@@positive_noun = ["Heaven", "King", "Lord", "angel", "flower", "happiness", "joy", "plum", "summer's day", "hero", "rose", "kingdom", "pony", ]
@@scenes = ["A camp near Forres", "A cavern In the middle a boiling cauldron", "A churchyard", "A churchyard in it a tomb belonging to the Capulets", "A desert place", "A hall in Capulets house", "A hall in the castle", "A Heath", "A heath near Forres", "A lane by the wall of Capulets orchard", "Alexandria A room in CLEOPATRAs palace", "Alexandria A room in the monument", "Alexandria Cleopatras palace", "Alexandria CLEOPATRAs palace", "Alexandria MARK ANTONYs camp", "Alexandria OCTAVIUS CAESARs camp", "Another part of the field", "Another part of the plain", "Another part of the platform", "Another part of the same", "Another room in the castle", "A park near the palace", "A plain in Denmark", "A plain in Syria", "A plain near Actium", "A public place", "A room in Capulets house", "A room in Polonius house", "A room in POLONIUS house", "A room in the castle", "A room of state in the castle", "A street", "Athens A room in MARK ANTONYs house", "Before Alexandria OCTAVIUS CAESARs camp", "Before Macbeths castle", "Between the two camps", "Camp before Florence", "Capulets orchard", "Country near Birnam wood", "Court of Macbeths castle", "Dunsinane Anteroom in the castle", "Dunsinane A room in the castle", "Dunsinane Before the castle", "Dunsinane Within the castle", "Egypt OCTAVIUS CAESARs camp", "Elsinore A platform before the castle", "Elsinore A room in the castle", "England Before the Kings palace", "Field of battle between the camps", "Fife Macduffs castle", "Florence Before the DUKEs palace", "Florence The DUKEs palace", "Florence The Widows house", "Florence Without the walls A tucket afar off", "Forres The palace", "Friar Laurences cell", "Hall in Capulets house", "Inverness Macbeths castle", "Juliets chamber", "Macbeths castle", "Mantua A street", "Marseilles A street", "Messina POMPEYs house", "Near Actium MARK ANTONYs camp", "Near Misenum", "OCTAVIUS CAESARs camp", "On board POMPEYs galley off Misenum", "Outside Macbeths castle", "Paris The KINGs palace", "Rome An antechamber in OCTAVIUS CAESARs house", "Rome OCTAVIUS CAESARs house", "Rome The house of LEPIDUS", "Rousillon Before the COUNTs palace", "Rousillon The COUNTs palace", "The country near Dunsinane", "The Florentine camp", "The palace", "The platform", "The Queens closet", "The same", "The same A monument", "The same Another room", "The same A room in the palace", "The same A street", "The same Before the palace", "The same Hall in the palace", "The same OCTAVIUS CAESARs house", "Under the walls of Alexandria", "Verona A public place", "Without the Florentine camp", ]
@@second_person_possessive = ["thine", "thy", "your", ]
@@second_person_reflexive = ["thyself", "yourself", ]
@@second_person = ["thee", "thou", "you", ]
@@take = ["receive", "take", "steal", "collect", "capture", "seize", "make off with", "nip", "swipe", "snatch", "snag", "snare", "grab", "usurp", ]
@@third_person_possessive = ["his", "her", "its", "their", ]
@@titles = ["All's Well That Ends Well", "Antony and Cleopatra", "As You Like It", "Comedy of Errors", "Coriolanus", "Cymbeline", "Hamlet", "Henry IV, Part I", "Henry IV, Part II", "Henry V", "Henry VI, Part I", "Henry VI, Part II", "Henry VI, Part III", "Henry VIII", "Julius Caesar", "King John", "King Lear", "Love's Labour's Lost", "Macbeth", "Measure for Measure", "Merchant of Venice", "Merry Wives of Windsor", "Midsummer Night's Dream", "Much Ado about Nothing", "Othello", "Pericles", "Richard II", "Richard III", "Romeo and Juliet", "Taming of the Shrew", "Tempest", "Timon of Athens", "Titus Andronicus", "Troilus and Cressida", "Twelfth Night", "Two Gentlemen of Verona", "Winter's Tale", ]
end
