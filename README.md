# YAML Reader 

A short and simple experiment to build a proof of concept for tree-based generation using LLMs. Something like that.

### Motivations

Nekoweb.org, I'm coming for you! I want to write a blog but I don't have the time to write entire blog posts. You know what's good at converting dot points to blog posts!? LLMS! 

Now if only you could provide context... and structure... and ease of use... for LLMs!? 

That's the core motivation behind this parser. It doesn't do anything by itself aside from assemble a template based on template blocks and primitives. The main focus here is to build a parser that is able to read specifically formatted YAML files and draw on existing block types.

#### The specific use case

Imagine on the LHS you had an input box. On the right, an output box.

LHS - add details like:
```yaml
  - type: article
    generate: true
    main_ideas: >
      $background
      Introduce yourself, don't talk about everything about yourself.
      Write a blog post that strictly follows these points:\n
      - This is a new blog you're writing\n
      - You've thought about writing it for a while
      - Rather than talking about boring stuff like goals for the blog or shiny smiley things, let's talk about something useful\n
      - One of the issues you've had in controls engineering is that there's often a lack of information regarding the subject\n
      - You'd like to change that moving forward.\n
      - This entire blog will be factual and come from your experiences as a Control Systems Engineer working at a System Integrator.\n
      - You've built this blog from an interesting array of technologies
      - And you've decided to use nekoweb.org in order to host it
      - the main reason for nekoweb is that the nostalgia from the 90's is nice.
      - This blog is special as it's automated with a new templating technique that you developed from scratch.
      - That's all for now. Signing off.
    children:
    - type: preface
      children: ~
```

And then on the right you get a live generation. Update "main ideas", get more generation. Combine this with more blocks, and then you have a cool templating thing!

### Core Concept

The idea behind this is motivated by trees and languages. The binary and software kind. I think it's easier to explain by example. Also, I don't think this parser is complete. I think it lacks some fundamental restrictions, since it feels too much like a repository. 

Each YAML file contains objects that follow this interface:

```YAML
type: <type>
...parameters
children: [children]
```

There are two special parameters, `template` and `generation`. In the parsing step, each object is loaded. Before it's consumed, its children are expanded. The results of the children (listed as `output`s) are attached to the parent as parameters.

When a child is expanded/loaded, the parent's keys (except immutable keys) are passed to the child. 

For example:

```YAML
root:
  type: blog
  template: $article
  children:                     (1a)
  - type: background
    goal: Introduce yourself, explain why you're doing this, explain the purpose of this blog.
    theme: An explainer document in the style of a blog post.
    structure: ~
    template: > 
      Background:\n             (1b)
      Goal: ${goal}\n
      Theme: ${theme}\n
      Structure: ${structure}\n
      $character
    children: ~
  - type: article
    generate: true              (1c)
    main_ideas: >
      $background               (1d)
      Introduce yourself, don't talk about everything about yourself.
      ...more content.
    children:
    - type: preface 
      children: ~
```

The root object contains an object of type **blog**. It also contains children (1a) which are expanded in order. 

> Sidenote: Expansion and terms
> 
> A quick sidenote, when I say "expanded", I really mean "processed" or "consumed", > or something like that. We're taking the object and looking into it, plopping > things into it, substituting, and basically doing a function call on it like `expand> (object)`
> 
> End of sidenote

When we look at the `$article` substitution, we can see that **blog** has a template:

```
$article
```

When we process blog, we look at its children. Once all its children are expanded (background and article), we get two results `background` and `article`. As the nodes are expanded in order, (1d) shows that we can use the result of the first child to substitute into the second child, **article**. This expands, and then results in the parameter `article` equal to a lengthy string that represents our article.

The special parameter on article is the `generate` parameter (1c). This is special in that it's not used as substitution, but rather, a flag. If this is true (or present), the template is fed into an LLM call.

In other words, if `generate` is true:
```
Result = LLM_Call(Template.substitute(parameters))
```

Otherwise:

```
Result = Template.substitute(parameters)
```

When we look at a *type* of an object, we search for its related primitive. In the case of **blog**, it's the following:

```yaml
primitives:
  ...other blocks
  - name: blog
    type: root
    doc_type: blog
    output: blog
    template: ~
```

This tells us that:
- The name of the primitive
- That it's of type 'root', which honestly means nothing at the moment.
- That it provides a parameter called `doc_type`
- That the output of this block is `blog`
- and that it has no template

This isn't that useful by itself, other than informing the system that we have a `doc_type` called blog. For example, what sort of document would I be reading right now if I said `$doc_type`? It'd be 'README'.

We then take the primitive and perform substitutions based on the instantiated object - plop in (1b) into the template. The result would be something like:

```yaml
blog:                   (2a)
    doc_type: blog
    template: >         (2b)
        Background:\n
        Goal: ${goal}\n
        Theme: ${theme}\n
        Structure: ${structure}\n
        $character
```

...and so on, and so forth. It's possible to generate entire blog posts with this system but I can't say I'm happy with it.

### Further Work

This isn't complete. The idea is there, but it's not complete. I'm looking at a more flushed-out version written in JS/TS rather than python, as I want to build a web interface for it.

`main.py` contains the code. Have fun?







