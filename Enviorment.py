import copy

from Genome import *


class Enviorment():
    def __init__(self, game, top=1, cut=1/2, randomness=0, inno=0, carry=1, mutation_rates=[0.8, 0.05, 0.01]):
        self.game = game

        self.randomness = randomness
        self.top = top
        self.population = []
        self.global_inno = inno
        self.input = game.input_size
        self.output = game.output_size
        self.prev_innovation = [[], []]
        self.cut = cut
        self.species = []
        self.carry = carry
        self.mutation_rates = mutation_rates

    def create(self, nr):
        new = []
        for i in range(nr):
            # TODO proper handling of possible functions.
            new.append(Genome(self.input, self.output, [identity], self.get_innovation))
        return self.speciate(new)

    def generation(self):
        species_champ = []
        species_surv = []
        averages = []
        # Raw scoring
        for s in self.species:
            for g in s:
                g.score = (self.game.run_genome(g) * random.gauss(1, self.randomness)) / len(s)
            s.sort(key=Genome.get_score(), reverse=True)
            species_champ.append(s[:self.carry])
            species_surv.append(s[:int(self.top * len(s))])
            averages.append(sum(g.score for g in s))
        # Allocating and creating offspring
        new_population = []
        self.prev_innovation = [[], []]
        total = sum(averages)
        new_genome_nr = sum(len(s) for s in self.species)
        for i in range(len(species_surv)):
            allocated = round((averages[i] / total) * new_genome_nr)
            # if allocated is less than 1 then the species does not get added to the next generation
            new_genome = self._repop(species_surv[i], allocated - len(species_champ[i]))
            new_population += (species_champ[:allocated][i] + new_genome)
        self.species = []
        self.speciate(new_population)
        return self.species

    def speciate(self, new):
        for g in new:
            found = False
            for s in self.species:
                g2 = s[0]
                if self.distance(g, g2) < self.cut:
                    s.append(g)
                    found = True
                    break
            if not found:
                self.species.append([g])
        return self.species

    def distance(self, g1, g2, c1=1, c2=1):  # TODO implement proper handling of c1 and c2
        weights = []
        exess_disjoint = 0
        for inno1 in g1.innovation_nrs:
            if inno1 in g2.innovation_nrs:
                weights.append(abs(
                    g1.genes[g1.innovation_nrs.index(inno1)].weight - g2.genes[g2.innovation_nrs.index(inno1)].weight))
            else:
                exess_disjoint += 1
        for inno2 in g2.innovation_nrs:
            if inno2 not in g1.innovation_nrs:
                exess_disjoint += 1
        return c1 * (exess_disjoint / max(len(g1.genes), len(g2.genes))) + c2 * (sum(weights) / len(weights))

    def _repop(self, s, nr):
        if nr < 1:
            return []
        genome = []
        for i in range(nr):
            genome.append(self.crossover(random.choice(s), random.choice(s)))
        return genome

    def crossover(self, g1, g2):
        fit = sorted([g1, g2], key=Genome.get_score())
        fit_ratio = fit[0].score / (fit[1].score + fit[0].score)
        new_nodes = copy.deepcopy(sorted([g1, g2], key=lambda x: len(x.nodes), reverse=True)[0])
        new_genes = []
        for g in fit[1].genes:
            if random.random() > fit_ratio:
                new_genes.append(copy.deepcopy(g))
            elif g.innovation in fit[0].innovation_nrs:
                new_genes.append(copy.deepcopy(fit[0].genes[fit[0].innovation_nrs.index(g.innovation)]))
        for g in fit[0].genes:
            if (g.innovation not in fit[1].innovation_nrs) and random.random() < fit_ratio:
                new_genes.append(copy.deepcopy(g))
        for g in new_genes:
            if not g.enabled and random.random() > .75:  # Random chance to reactivate genes.
                g.enable()
        b = Genome(self.input, self.output, [identity], self.get_innovation)
        b.genes = new_genes
        b.nodes = new_nodes
        b.relayer()
        b.mutate(self.mutation_rates[0], self.mutation_rates[1], self.mutation_rates[2])
        return b

    def get_innovation(self, in_node, out_node):

        if [in_node, out_node] not in self.prev_innovation[0]:
            self.prev_innovation[0].append([in_node, out_node])
            self.global_inno += 1
            self.prev_innovation[1].append(self.global_inno)
            return self.global_inno
        else:
            return self.prev_innovation[1][self.prev_innovation[0].index([in_node, out_node])]
